import configparser
from logging import getLogger, FileHandler, Formatter, INFO
import warnings
warnings.filterwarnings('ignore')


def get_logger():
    logger = getLogger('log.log')
    logger.setLevel(INFO)
    file_handler = FileHandler('log.log')
    file_handler.setLevel(INFO)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    DB_NAME = config.get('General', 'DB_NAME')
    SEED_PAGE_NAME = config.get('General', 'SEED_PAGE_NAME')
    SIM_THRESHOLD = config.get('General', 'SIM_THRESHOLD')
    LANG_CODES = config.get('General', 'LANG_CODES').split(',')
    SBERT_MODEL_NAME = config.get('General', 'SBERT_MODEL_NAME')

    config_values = {
        'DB_NAME': DB_NAME,
        'SEED_PAGE_NAME': SEED_PAGE_NAME,
        'SIM_THRESHOLD': SIM_THRESHOLD,
        'LANG_CODES': LANG_CODES,
        'SBERT_MODEL_NAME': SBERT_MODEL_NAME
    }

    return config_values


logger = get_logger()

config = read_config()
