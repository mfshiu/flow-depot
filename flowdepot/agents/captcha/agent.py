# flowdepot\agents\captcha\agent.py
# pip install --upgrade openai>=1.40.0

import base64
import magic
import mimetypes
from openai import OpenAI
import os
from pathlib import Path
import tempfile
import yaml
import threading
import logging
from flowdepot.app_logger import init_logging
from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel
from flowdepot.agents.topics import AgentTopics

logger: logging.Logger = init_logging()

# 全域鎖（單一進入，後來者等待）
_OCR_GLOBAL_LOCK = threading.RLock()




class CaptchaService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.openai_client = OpenAI(api_key=agent_config.get("openai_api_key", ""))
        logger.info(f"OpenAI API Key: {self.openai_client.api_key}")

        # Create "temp" folder in current execution path if it doesn't exist for audio files.
        self.temp_root = Path.cwd() / "temp"
        self.temp_root.mkdir(exist_ok=True)

        # 可調整：鎖等待逾時（秒）；None=無限等
        self.lock_timeout = agent_config.get("lock_timeout_sec", None)


    def on_activate(self):
        self.subscribe(AgentTopics.CAPTCHA_RECOGNIZE, "str", self.recognize_captcha)


    
    def recognize_captcha(self, topic: str, pcl: BinaryParcel):
        """
        使用全域鎖，確保同時間僅一個 OCR 處理；其他呼叫會等待鎖釋放。
        """
        # 先嘗試非阻塞；若忙碌則紀錄並阻塞等待
        acquired = _OCR_GLOBAL_LOCK.acquire(blocking=False)
        if not acquired:
            logger.info("[CaptchaService] OCR busy, waiting for global lock...")
            # 若設定 lock_timeout，則等待到逾時；否則無限等待
            acquired = _OCR_GLOBAL_LOCK.acquire(timeout=self.lock_timeout) if self.lock_timeout else _OCR_GLOBAL_LOCK.acquire()
        if not acquired:
            # 逾時（若設定了 lock_timeout）
            return {"topic": topic, "error": "ocr_lock_timeout"}

        try:
            captcha_info: dict = pcl.content or {}
            img_content = captcha_info.get('content')
            file_mime_type = captcha_info.get('mime_type')

            mime = magic.Magic(mime=True)
            response = {}
            try:
                if not file_mime_type:
                    file_mime_type = mime.from_buffer(img_content)
                logger.info(f'file_mime_type: {file_mime_type}')
                if file_mime_type.startswith('image/'):
                    response['text'] = self._recognize_captcha(topic, img_content, file_mime_type.split('/')[-1])
                    response['mime_type'] = file_mime_type
                    response['topic'] = topic
                else:
                    logger.warning('Content is not image.')
            except Exception as ex:
                logger.exception(ex)
                response['error'] = str(ex)

            return response

        finally:
            _OCR_GLOBAL_LOCK.release()


    
    def _recognize_captcha(self, _, content, file_type):
        
        def to_data_url(path: str) -> str:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{file_type};base64,{b64}"
    

        def ocr_id(image_path: str) -> str:
            """用 gpt-4o-mini 進行 OCR，回傳純文字"""
            data_url = to_data_url(image_path)
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
            )
            content = resp.choices[0].message.content
            return content.strip() if content else ""
       
        with tempfile.NamedTemporaryFile(mode="wb", suffix=f".{file_type}", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            file_path = Path(tmp.name)

        try:
            recognized_text = ocr_id(str(file_path))
        finally:
            if file_path.exists():
                os.remove(file_path)

        return recognized_text
