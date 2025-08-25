import re
from urllib import response
import magic
import os
from pathlib import Path
import tempfile
import torch
import whisper

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel
from agents.topics import AgentTopics

import logging
from flowdepot.app_logger import init_logging
logger:logging.Logger = init_logging()



class SttService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.whisper_model_name = agent_config["whisper_model"]
        
        # Create "temp" folder in current execution path if it doesn't exist for audio files.
        self.temp_root = Path.cwd() / "temp"
        self.temp_root.mkdir(exist_ok=True)


    def on_activate(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.warning(f'Device of Whisper: {device}')

        # Continue here..
        logger.warning(f'Loading model: {self.whisper_model_name}')
        self.whisper_model = whisper.load_model(self.whisper_model_name, device=device)

        self.subscribe(AgentTopics.STT_CONTENT, "str", self.transcribe_content)


    def transcribe_content(self, topic:str, pcl:BinaryParcel):
        audio_info: dict = pcl.content or {}
        content = audio_info.get('content')

        mime = magic.Magic(mime=True)
        response = {}
        try:
            file_mime_type = mime.from_buffer(content)
            logger.info(f'file_mime_type: {file_mime_type}')
            if file_mime_type.startswith('audio/') or file_mime_type.startswith('video/'):
                response['text'] = self._transcribe_content(topic, content, file_mime_type.split('/')[-1])
                response['mime_type'] = file_mime_type
                response['topic'] = topic
            else:
                logger.warning(f'Content is not audio or video.')
        except Exception as ex:
            logger.exception(ex)
            response['error'] = str(ex)
            
        return response


    def _transcribe_content(self, _, content, audio_type):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=f".{audio_type}", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            file_path = Path(tmp.name)

        try:
            result = self.whisper_model.transcribe(str(file_path))
            transcribed_text = result["text"]
        finally:
            # 確保即使轉換錯誤也會清理檔案
            if file_path.exists():
                os.remove(file_path)

        return transcribed_text
    
    
def main():
    # 初始化 STT Agent
    agent_config = {
        "whisper_model": "base"  # tiny, base, small, medium, large
    }
    stt_agent = SttService("stt-agent", agent_config)
    stt_agent.on_activate()

    # 載入測試音檔
    audio_path = Path(r"flowdepot\agents\stt\sample_apeech.mp3")
    with audio_path.open("rb") as f:
        content = f.read()

    # 模擬接收到的 TextParcel
    parcel = BinaryParcel(content={'content': content})

    # 呼叫轉錄函式
    topic = "Test/STT"
    result = stt_agent.transcribe_content(topic, parcel)

    print("📜 Transcribed text:")
    print(result)


if __name__ == "__main__":
    main()
    