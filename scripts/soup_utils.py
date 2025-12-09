"""
Utils to load, download and save a BeautifulSoup soup containing a wikipedia html page.

Also, utils to extract paragraph text and links from a soup.
"""

import os
import requests
import pickle
import bs4
from data_utils import soups_path, paragraphs_path
from dotenv import load_dotenv

load_dotenv('../.env')


def get_html_url(page_name: str, lang: str='en') -> str:
    "Given a page name and a lang code, return a formated wikipedia url"
    return f'https://api.wikimedia.org/core/v1/wikipedia/{lang}/page/{page_name}/html'


def get_headers() -> dict:
    "load the env variables containing the wikipedia API keys"
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    APP_NAME = os.getenv("APP_NAME")
    EMAIL = os.getenv("EMAIL")
    HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}
    return HEADERS


def download_soup(page_name: str) -> bs4.BeautifulSoup:
    "Given a page name, request a wikipedia url and return the parsed html page as a bs4 soup."
    HEADERS = get_headers()
    html_url = get_html_url(page_name)
    response = requests.get(html_url, headers=HEADERS)
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    return soup


def get_soup(page_name: str) -> bs4.BeautifulSoup:
    "Given a page name, either load the saved soup or download the soup."
    fn = f'{page_name}.pkl'
    if fn in os.listdir(soups_path):
        with open(os.path.join(soups_path, fn), "rb") as f:
            soup = pickle.load(f)
    else:
        soup = download_soup(page_name)
    return soup


def save_soup(page_name: str, soup: bs4.BeautifulSoup) -> None:
    "Given a page name and a soup, pickle and save the soup."
    fn = f'{page_name}.pkl'
    with open(os.path.join(soups_path, fn), "wb") as f:
        pickle.dump(soup, f)


def get_paragraphs_text(soup: bs4.BeautifulSoup) -> list:
    "Given a soup, return the text of all paragraphs."
    paragraphs = []
    try:
        for p in soup.find_all('p'):
            paragraphs.append(p.text)
    except Exception as e:
        print(str(e))
    return paragraphs


def save_paragraphs(page_name: str, paragraphs: list) -> None:
    "Given a page name and a list of paragraphs, save them to a text file."
    fn = f'{page_name}.txt'
    fn_path = os.path.join(paragraphs_path, fn)
    with open(fn_path, "w") as f:
        f.write('\n'.join(paragraphs))


def get_internal_page_names(soup: bs4.BeautifulSoup) -> list:
    """
    Given a soup, extract all unique links from the page's content.
    
    Specifically, get all hrefs from <a> tags in <p> elements.

    The goal is to get related page names only from the page's content,
    excluding links to category pages and other less relevant links.
    
    """
    # List of characters or words to ignore when collecting page names
    exclude = ['#', '%', ':', '=', 'File:', 'Help:', 'List_of']

    hrefs = set()
    for p in soup.find_all('p'):
        for a in p.find_all('a'):
            try:
                href = a.get('href')
                if href.startswith('.') and not any(e in href for e in exclude):
                    hrefs.add(href[2:])
            except AttributeError:
                continue
    return list(hrefs)
