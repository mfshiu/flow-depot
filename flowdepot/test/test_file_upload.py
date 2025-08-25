# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 17:00

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import unittest
import yaml

import logging
from flowdepot.app_logger import init_logging
logger:logging.Logger = init_logging()

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel, Parcel
from agents.topics import AgentTopics


config_path = os.path.join(os.getcwd(), 'config', 'system.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    agent_config = yaml.safe_load(f) or {}



class TestAgent(unittest.TestCase):
    file_id = None
    filename = None
    
    class ValidationAgent(Agent):
        def __init__(self):
            super().__init__(name='main', agent_config=agent_config)


        def on_activate(self):
            self.subscribe('file_uploaded')
            
            filename = 'test_img1.jpg'
            with open(os.path.join(os.getcwd(), 'flowdepot', 'test', 'data', filename), 'rb') as file:
                content = file.read()
            pcl = BinaryParcel({
                'content': content,
                'filename': filename}, 'file_uploaded')
            self.publish(AgentTopics.FILE_UPLOAD , pcl)


        def on_message(self, topic:str, pcl:Parcel):
            file_info:dict = pcl.content or {}
            logger.debug(self.M(f"topic: {topic}, file_info: {file_info}"))

            TestAgent.file_id = file_info.get('file_id')
            TestAgent.filename = file_info.get('filename')


    def setUp(self):
        home_directory = os.path.join(os.getcwd(), '_upload')
        if not os.path.exists(home_directory):
            os.mkdir(home_directory)

        self.validation_agent = TestAgent.ValidationAgent()
        self.validation_agent.start_thread()


    def _do_test_1(self):
        logger.debug(f'file_id: {TestAgent.file_id}')
        self.assertTrue(TestAgent.file_id)
        self.assertEqual('test_img1.jpg', TestAgent.filename)


    def test_1(self):
        time.sleep(3)

        try:
            self._do_test_1()
        except Exception as ex:
            logger.exception(ex)
            self.assertTrue(False)


    def tearDown(self):
        self.validation_agent.terminate()



if __name__ == '__main__':
    unittest.main()
