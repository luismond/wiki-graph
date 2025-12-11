import os
import warnings
warnings.filterwarnings('ignore')


BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "data")
CSV_PATH = os.path.join(DATA_PATH, "csv")
TXT_PATH = os.path.join(DATA_PATH, "txt")
EMBS_PATH = os.path.join(DATA_PATH, "embs")
PARAGRAPHS_PATH = os.path.join(DATA_PATH, "paragraphs")
SOUPS_PATH = os.path.join(DATA_PATH, "soups")

page_relationships_file = os.path.join(CSV_PATH, 'page_relationships.csv')
