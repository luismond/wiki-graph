import os
from dotenv import load_dotenv
import warnings
from datetime import datetime
from logging import getLogger, FileHandler, Formatter, INFO

warnings.filterwarnings('ignore')
load_dotenv()

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

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
DB_NAME = os.getenv("DB_NAME")

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': f'{APP_NAME} ({EMAIL})'
    }

current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
