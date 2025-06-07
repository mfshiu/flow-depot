# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 17:00

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import unittest
import yaml

import logging
from app_logger import init_logging
logger:logging.Logger = init_logging()

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel, Parcel
from agents.topics import AgentTopics



class TestAgent(unittest.TestCase):
    stt_result_text = None
    
    class ValidationAgent(Agent):
        def __init__(self):
            config_path = os.path.join(os.getcwd(), 'config', 'system.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                agent_config = yaml.safe_load(f) or {}
            super().__init__(name='main', agent_config=agent_config)


        def on_activate(self):
            self.subscribe('stt_result')
            
            filename = 'sample_apeech.mp3'
            with open(os.path.join(os.getcwd(), 'test', 'data', filename), 'rb') as file:
                content = file.read()
            pcl = BinaryParcel({
                'content': content,}, 'stt_result')
            self.publish(AgentTopics.STT_CONTENT , pcl)


        def on_message(self, topic:str, pcl:Parcel):
            stt_resp:dict = pcl.content or {}
            logger.debug(self.M(f"topic: {topic}, stt_resp: {stt_resp}"))

            TestAgent.stt_result_text = stt_resp.get('text', '')


    def setUp(self):
        self.validation_agent = TestAgent.ValidationAgent()
        self.validation_agent.start_thread()


    def _do_test_1(self):
        logger.debug(f'file_id: {TestAgent.stt_result_text}')
        self.assertTrue(TestAgent.stt_result_text)


    def test_1(self):
        time.sleep(5)

        try:
            self._do_test_1()
        except Exception as ex:
            logger.exception(ex)
            self.assertTrue(False)


    def tearDown(self):
        self.validation_agent.terminate()



if __name__ == '__main__':
    unittest.main()
