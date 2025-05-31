from agentflow.core.agent import Agent

import hashlib
import mimetypes
import os
import random
import time
import uuid

from agentflow.core.parcel import BinaryParcel

import logging
from agents import LOGGER_NAME
logger:logging.Logger = logging.getLogger(LOGGER_NAME)
if not logger.hasHandlers():
    from app_logger import init_logging
    logger:logging.Logger = init_logging()

logger.info(f"[FileService] Logger initialized: {logger.name}, Level: {logger.level}")
print(f"[FileService] Logger: {logger.name}, Level: {logger.level}")




class FileService(Agent):
    TOPIC_FILE_UPLOAD = "FileUpload/FileService"
    
    
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.home_directory = agent_config['agent']['home_directory']


    def _generate_file_id(self, filename):        
        current_time = str(int(time.time() * 1000))
        combined_input = filename + current_time + str(random.randint(0, 999)).zfill(3)
        sha1_hash = hashlib.sha1(combined_input.encode()).hexdigest()
        generated_uuid = str(uuid.UUID(sha1_hash[:32])).replace('-', '')
        
        return generated_uuid


    def handle_file_upload(self, topic:str, pcl:BinaryParcel):
        file_info: dict = pcl.content or {}
        content = file_info.get('content')
        logger.info(f"topic: {topic}, filename: {file_info.get('filename')}, content size: {len(content or b'')}")
        # print(f"topic: {topic}, filename: {file_info.get('filename')}, content size: {len(content or b'')}")

        filename = file_info.get('filename')
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename is required and must be a non-empty string")
        file_id = self._generate_file_id(filename)
        mime_type, encoding = mimetypes.guess_type(url=filename)
        logger.debug(f"file_id: {file_id}, filename: {filename}, mime_type: {mime_type}, encoding: {encoding}")
        
        
        file_dir = os.path.join(self.home_directory, file_id[:2], file_id[2:4])
        # file_dir = os.path.join(self.home_directory, file_id[:2])
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_path = os.path.join(file_dir, f"{file_id}-{filename}")
        content = file_info.get('content')
        open_mode = "w" if isinstance(content, str) else "wb"
        with open(file_path, open_mode) as fp:
            fp.write(content)
        logger.info(f"filename: {filename} is saved.")

        result = {k: v for k, v in file_info.items() if k != 'content'}
        result.update({
            'file_id': file_id,
            'filename': filename,
            'mime_type': mime_type,
            'encoding': encoding,
            'file_path': file_path,
        })
        logger.info(f"result: {result}")
        return result


    def on_activate(self):
        logger.info(f"subscribe: {FileService.TOPIC_FILE_UPLOAD}")
        self.subscribe(FileService.TOPIC_FILE_UPLOAD, "str", self.handle_file_upload)
