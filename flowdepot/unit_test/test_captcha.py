import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mimetypes
import time
import unittest
import yaml

import logging
from flowdepot.app_logger import init_logging
logger:logging.Logger = init_logging()

from agentflow.core.agent import Agent
from agentflow.core.parcel import BinaryParcel, Parcel
from agents.topics import AgentTopics


config_path1 = os.path.join(os.getcwd(), 'config', 'system.yaml')
with open(config_path1, 'r', encoding='utf-8') as f:
    agent_config = yaml.safe_load(f) or {}
config_path2 = os.path.join(os.getcwd(), 'flowdepot', 'agents', 'captcha', 'agent.yaml')
with open(config_path2, 'r', encoding='utf-8') as f:
    agent_config.update(yaml.safe_load(f))



class TestAgent(unittest.TestCase):
    answer_text = ''
    
    class ValidationAgent(Agent):
        def __init__(self):
            super().__init__(name='main', agent_config=agent_config)


        def on_activate(self):
            self.subscribe('return_topic')
            
            filename = 'captcha-56839.png'
            mime, _ = mimetypes.guess_type(filename)
            with open(os.path.join(os.getcwd(), 'flowdepot', 'unit_test', 'data', filename), 'rb') as file:
                content = file.read()
            pcl = BinaryParcel({
                'content': content,
                'mime_type': mime}, 'return_topic')
            self.publish(AgentTopics.CAPTCHA_RECOGNIZE , pcl)


        def on_message(self, topic:str, pcl:Parcel):
            result:dict = pcl.content or {}
            logger.debug(self.M(f"topic: {topic}, result: {result}"))

            TestAgent.answer_text = result.get('text') or ''


    def setUp(self):
        self.validation_agent = TestAgent.ValidationAgent()
        self.validation_agent.start_thread()


    def _do_test_1(self):
        logger.debug(f'answer_text: {TestAgent.answer_text}')
        self.assertEqual('56839', TestAgent.answer_text)


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
