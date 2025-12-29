import os
from dotenv import load_dotenv
import warnings
from datetime import datetime
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

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
DB_NAME = os.getenv("DB_NAME")
SEED_PAGE_NAME = os.getenv("SEED_PAGE_NAME")
SIM_THRESHOLD = os.getenv("SIM_THRESHOLD")
LANG_CODES = os.getenv("LANG_CODES").split(',')
SBERT_MODEL_NAME = os.getenv("SBERT_MODEL_NAME")

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': f'{APP_NAME} ({EMAIL})'
    }

current_datetime_str = datetime.now().strftime('%Y-%m-%d')
