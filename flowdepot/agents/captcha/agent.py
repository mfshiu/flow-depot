# pip install --upgrade openai>=1.40.0
 
import base64
import magic
import mimetypes
from openai import OpenAI
import os
from pathlib import Path
import tempfile
import yaml

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel
from agents.topics import AgentTopics

import logging
from flowdepot.app_logger import init_logging
logger:logging.Logger = init_logging()

openai_client = OpenAI()
print("使用的 OpenAI API Key:", openai_client.api_key)



class CaptchaService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        openai_client.api_key = agent_config.get("openai_api_key", "")
        logger.info(f"OpenAI API Key: {openai_client.api_key}")
        
        # Create "temp" folder in current execution path if it doesn't exist for audio files.
        self.temp_root = Path.cwd() / "temp"
        self.temp_root.mkdir(exist_ok=True)


    def on_activate(self):
        self.subscribe(AgentTopics.CAPTCHA_RECOGNIZE, "str", self.recognize_captcha)


    def recognize_captcha(self, topic:str, pcl:BinaryParcel):
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


    def _recognize_captcha(self, _, content, file_type):
    
    
        # def to_data_url(path: str) -> str:
        #     mime, _ = mimetypes.guess_type(path)
        #     if not mime: mime = "image/png"
        #     with open(path, "rb") as f:
        #         b64 = base64.b64encode(f.read()).decode("utf-8")
        #     return f"data:{mime};base64,{b64}"
        def to_data_url(path: str) -> str:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{file_type};base64,{b64}"
    

        def ocr_id(image_path: str) -> str:
            """用 gpt-4o-mini 進行 OCR，回傳純文字"""
            data_url = to_data_url(image_path)
            resp = openai_client.chat.completions.create(
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
    
    
def main():
    # 初始化 STT Agent
    agent_config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", "")  # 請設定你的 OpenAI API Key
    }
    with open(r"flowdepot\agents\captcha\agent.yaml", "r", encoding="utf-8") as f:
        agent_config: dict = yaml.safe_load(f)
    agent = CaptchaService(agent_config['name'], agent_config)
    agent.on_activate()

    # 載入測試圖檔
    img_path = Path(r"flowdepot\agents\captcha\captcha-73634.png")
    mime, _ = mimetypes.guess_type(img_path)
    with img_path.open("rb") as f:
        content = f.read()

    # 模擬接收到的 Parcel
    parcel = BinaryParcel(content={'content': content, 'mime_type': mime})

    # 呼叫轉錄函式
    topic = "Captcha/RecognizeTest"
    result = agent.recognize_captcha(topic, parcel)

    print("📜 Recognize text:")
    print(result)


if __name__ == "__main__":
    main()
    