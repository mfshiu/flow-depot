# flowdepot\agents\captcha\agent.py
# pip install --upgrade openai>=1.40.0

import base64
import magic
import mimetypes
from openai import OpenAI
import os, time, threading
from pathlib import Path
import tempfile
import yaml

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel
from flowdepot.agents.topics import AgentTopics

import logging
from flowdepot.app_logger import init_logging
logger: logging.Logger = init_logging()

# 全域鎖 + 上次完成時間
_OCR_LOCK = threading.RLock()
_LAST_FINISH_TS = 0.0
_MIN_INTERVAL = 2.0   # 秒




class CaptchaService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.openai_client = OpenAI(api_key=agent_config.get("openai_api_key", ""))
        logger.info(f"OpenAI API Key: {self.openai_client.api_key}")

        # Create "temp" folder in current execution path if it doesn't exist
        self.temp_root = Path.cwd() / "temp"
        self.temp_root.mkdir(exist_ok=True)


    def on_activate(self):
        self.subscribe(AgentTopics.CAPTCHA_RECOGNIZE, "str", self.recognize_captcha)


    
    def recognize_captcha(self, topic: str, pcl: BinaryParcel):
        global _LAST_FINISH_TS
        with _OCR_LOCK:
            # 檢查距離上次完成是否 >= 2 秒
            now = time.time()
            elapsed = now - _LAST_FINISH_TS
            if elapsed < _MIN_INTERVAL:
                wait_sec = _MIN_INTERVAL - elapsed
                logger.info(f"[CaptchaService] Waiting {wait_sec:.2f}s to enforce min interval")
                time.sleep(wait_sec)

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
                        logger.warning(f'Content is not image.')
                except Exception as ex:
                    logger.exception(ex)
                    response['error'] = str(ex)

                return response
            finally:
                _LAST_FINISH_TS = time.time()


    
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
