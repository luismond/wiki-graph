from dotenv import dotenv_values
import warnings
from logging import getLogger, FileHandler, Formatter, INFO
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


logger = get_logger()


# env variables
config = {**dotenv_values()}


# Wikipedia access data
ACCESS_TOKEN = config["ACCESS_TOKEN"]
APP_NAME = config["APP_NAME"]
EMAIL = config["EMAIL"]
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': f'{APP_NAME} ({EMAIL})'
    }
