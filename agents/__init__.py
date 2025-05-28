from datetime import datetime
import logging
import os
import signal
import time
import yaml


LOGGER_NAME = os.environ.get('LOGGER_NAME', 'flowdepot')


def load_config_from_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config_path = os.path.join(os.getcwd(), 'config', 'default.yaml')
config = load_config_from_yaml(config_path)


def get_agent_config():
    global config

    broker_name = config['broker']['broker_name']

    agent_config = {
        'version': config['system']['version'],
        'broker': {
            **config['broker'].get(broker_name, {})
        }
    }

    return agent_config


def wait_agent(agent):
    def signal_handler(signal, frame):
        agent.terminate()
    signal.signal(signal.SIGINT, signal_handler)

    time.sleep(1)
    dot_counter = 0
    minute_tracker = datetime.now().minute

    while agent.is_active():
        time.sleep(1)

        dot_counter += 1
        if dot_counter % 6 == 0:
            print('.', end='', flush=True)

        current_minute = datetime.now().minute
        if current_minute != minute_tracker:
            print(f"{datetime.now().strftime('%H:%M')}", end='', flush=True)
            minute_tracker = current_minute
    print()
