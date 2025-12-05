import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')
load_dotenv()

# ENV VARS
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}

# MODELS
MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')

# LANGUAGES
LANG = 'en'
