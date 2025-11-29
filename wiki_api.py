"""
wiki_api.py

A script to fetch and parse the HTML content of a Wikipedia page using the Wikimedia API.
Retrieves the page's HTML, extracts all paragraphs, and collects their text.

Environment Variables Required:
- ACCESS_TOKEN: Your Wikimedia API access token.
- APP_NAME: The name of your application (for User-Agent).
- EMAIL: Contact email address (for User-Agent).
"""

import os
import requests
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")

headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}

url = 'https://api.wikimedia.org/core/v1/wikipedia/en/page/Earth/html'

response = requests.get(url, headers=headers)
data = response.text
soup = bs(data)

def get_paragraphs_text(soup):
    return [p.text for p in soup.find_all('p')]

ps = get_paragraphs_text(soup)

