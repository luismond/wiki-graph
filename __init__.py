import os
from dotenv import load_dotenv
import warnings

warnings.filterwarnings('ignore')
load_dotenv()


ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': f'{APP_NAME} ({EMAIL})'
    }

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "data")
TXT_PATH = os.path.join(DATA_PATH, "txt")
SOUPS_PATH = os.path.join(DATA_PATH, "soups")
