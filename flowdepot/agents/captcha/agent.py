# flowdepot\agents\captcha\agent.py

# pip install --upgrade openai>=1.40.0

import base64
import hashlib
import mimetypes
import os
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from time import monotonic, sleep

from openai import OpenAI

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel
from flowdepot.agents.topics import AgentTopics

import logging
from flowdepot.app_logger import init_logging
logger: logging.Logger = init_logging()


# ------- 小工具 -------

def _guess_mime_from_ext(filename: str | None) -> str | None:
    if not filename:
        return None
    mime, _ = mimetypes.guess_type(filename)
    return mime


def _to_data_url(image_bytes: bytes, mime: str) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()



# ------- LRU 迷你快取（避免重複圖同時湧入） -------

class _LRU:
    def __init__(self, maxsize=256, ttl=60.0):
        self.maxsize = maxsize
        self.ttl = ttl
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, dict]] = {}

    def get(self, k: str):
        with self._lock:
            v = self._store.get(k)
            if not v:
                return None
            t, data = v
            if monotonic() - t > self.ttl:
                self._store.pop(k, None)
                return None
            return data

    def set(self, k: str, value: dict):
        with self._lock:
            if len(self._store) >= self.maxsize:
                # 粗略移除過期或最舊的
                oldest = min(self._store.items(), key=lambda x: x[1][0])[0]
                self._store.pop(oldest, None)
            self._store[k] = (monotonic(), value)



# ------- 服務本體 -------



class CaptchaService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)

        api_key = agent_config.get("openai_api_key", "") or os.getenv("OPENAI_API_KEY", "")
        self.openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized.")

        # 併發控制（避免 API/CPU 爆掉）；可視硬體與配額調整
        self.max_workers = int(agent_config.get("max_workers", 2))
        self.max_concurrency = int(agent_config.get("max_concurrency", 2))
        self._pool = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="captcha")
        self._sem = threading.Semaphore(self.max_concurrency)

        # 去重快取（相同圖片 60 秒內直接回覆）
        self._cache = _LRU(maxsize=512, ttl=float(agent_config.get("dedup_ttl_sec", 60)))

        # 逾時/重試設定
        self.req_timeout_sec = float(agent_config.get("request_timeout_sec", 20))
        self.max_retries = int(agent_config.get("max_retries", 3))
        self.retry_backoff_sec = float(agent_config.get("retry_backoff_sec", 0.8))

        # 可選：建立 temp 目錄（若後續想落檔）
        self.temp_root = Path.cwd() / "temp"
        self.temp_root.mkdir(exist_ok=True)



    def on_activate(self):
        self.subscribe(AgentTopics.CAPTCHA_RECOGNIZE, "str", self.recognize_captcha)



    def recognize_captcha(self, topic: str, pcl: BinaryParcel):
        """
        同步介面維持不變；內部以 thread pool + semaphore 限流。
        收到暴衝時：排隊 -> 執行 -> 回傳。
        """
        captcha_info: dict = pcl.content or {}
        img_bytes: bytes | None = captcha_info.get("content")
        file_mime_type: str | None = captcha_info.get("mime_type")
        filename: str | None = captcha_info.get("filename")  # 若上游可提供，利於猜測 MIME

        response: dict = {"topic": topic}

        try:
            if not img_bytes:
                raise ValueError("Missing image content.")

            # 先查快取（圖片哈希）
            key = _sha1(img_bytes)
            cached = self._cache.get(key)
            if cached:
                logger.info("Hit captcha cache.")
                return cached | response

            # 判斷 MIME：優先來自上游，其次副檔名；仍無則預設 image/png
            mime = file_mime_type or _guess_mime_from_ext(filename) or "image/png"
            if not mime.startswith("image/"):
                raise ValueError(f"Unsupported mime type: {mime}")

            data_url = _to_data_url(img_bytes, mime)

            # 以 semaphore 限制同時進行的 OpenAI 請求數
            def _job():
                with self._sem:
                    return self._ocr_with_retry(data_url)

            fut = self._pool.submit(_job)
            text = fut.result(timeout=self.req_timeout_sec + self.max_retries * (self.retry_backoff_sec + 1))

            result = {"text": text.strip(), "mime_type": mime}
            self._cache.set(key, result)
            return result | response

        except TimeoutError:
            logger.exception("Captcha OCR timed out.")
            response["error"] = "timeout"
            return response
        except Exception as ex:
            logger.exception(ex)
            response["error"] = str(ex)
            return response



    def _ocr_with_retry(self, data_url: str) -> str:
        """
        對 OpenAI 進行重試（指數退避），並加上請求逾時。
        """
        delay = self.retry_backoff_sec
        last_err = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # 設定 temperature=0，要求純文字
                resp = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "請輸出圖片中的純文字，不要任何解釋或符號。"},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }],
                    temperature=0,
                    timeout=self.req_timeout_sec,  # 需要 openai>=1.40.0
                )
                content = (resp.choices[0].message.content or "").strip()
                if content:
                    return content
                # 空字串也重試一次
                last_err = RuntimeError("empty OCR result")
                raise last_err

            except Exception as e:
                last_err = e
                if attempt >= self.max_retries:
                    break
                sleep(delay)
                delay *= 1.6  # 指數退避

        raise last_err or RuntimeError("OCR failed")
