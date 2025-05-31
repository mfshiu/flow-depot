# -*- coding: utf-8 -*-
from colorama import init, Fore, Style
import logging
import os
import yaml


LOGGING_LEVEL_VERBOSE = int(logging.DEBUG / 2)
logging.addLevelName(LOGGING_LEVEL_VERBOSE, "VERBOSE")

def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(LOGGING_LEVEL_VERBOSE):
        self._log(LOGGING_LEVEL_VERBOSE, message, args, **kwargs, stacklevel=2)
logging.Logger.verbose = verbose


def init_logging(config_path=None):
    config_path = config_path or os.path.join(os.getcwd(), 'config', 'system.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        log_config = (yaml.safe_load(f) or {}).get('logging', {})

    log_name = log_config.get('name', 'flowdepot')
    log_level = log_config.get('level', logging.DEBUG)
        
    os.environ['LOGGER_NAME'] = log_name
    os.environ['LOGGER_LEVEL'] = str(log_level)
    
    logger = logging.getLogger(log_name)
    if not logger.hasHandlers():
        fmt = '%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)15s:%(lineno)03d %(funcName)15s) %(message)s'
        datefmt = '%m-%d %H:%M:%S'
        handler = logging.StreamHandler()
        formatter = ColorFormatter(fmt, datefmt)
        # formatter = logging.Formatter(fmt, datefmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(log_level)
        
    return logger



init(autoreset=True)    # Initialize colorama for Windows

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'C': Fore.MAGENTA,
        'E': Fore.RED,
        'W': Fore.YELLOW,
        'I': Fore.CYAN,
        'D': Fore.WHITE,
        'V': Fore.LIGHTBLACK_EX
    }

    def format(self, record):
        level_char = record.levelname[0]  # Get first letter of log level
        color = self.LEVEL_COLORS.get(level_char, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"



if __name__ == "__main__":
    logger = init_logging()
    # logger = logging.getLogger('flowdepot')
    logger.debug("This is a debug message.")
    logger.verbose("This is a verbose message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
