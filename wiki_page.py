"""
Utils to load, download and save a BeautifulSoup soup containing a wikipedia html page.

Also, utils to extract paragraph text and links from a soup.
"""

import os
import re
import requests
import pickle
import bs4
from dotenv import load_dotenv
from gliner import GLiNER
from __init__ import DATA_PATH
# # Initialize GLiNER with the base model
# model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}

paragraphs_path = os.path.join(DATA_PATH, "paragraphs")
soups_path = os.path.join(DATA_PATH, "soups")


class WikiPage:
    """
    Represents a single Wikipedia page, including methods to download, parse, and extract links and paragraphs.
    """
    def __init__(self, page_name: str, lang: str = 'en'):
        self.page_name = page_name
        self.lang = lang
        self.soup = None
        self.paragraphs = []
        self.shortdescription = None
        self.load()

    def load(self):
        self.soup = self.get_soup()
        self.paragraphs = self.get_paragraphs_text()
        self.shortdescription = self.get_shortdescription()

    def __repr__(self):
        return f"<WikiPage {self.page_name}>"

    def get_soup(self) -> bs4.BeautifulSoup:
        "Given a page name, either load the saved soup or download the soup."
        fn = f'{self.page_name}.pkl'
        if fn in os.listdir(soups_path):
            with open(os.path.join(soups_path, fn), "rb") as f:
                soup = pickle.load(f)
        else:
            soup = self.download_soup()
        return soup

    def download_soup(self) -> bs4.BeautifulSoup:
        "Given a page name, request a wikipedia url and return the parsed html page as a bs4 soup."
        html_url = f'https://api.wikimedia.org/core/v1/wikipedia/{self.lang}/page/{self.page_name}/html'
        response = requests.get(html_url, headers=HEADERS, timeout=180)
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        return soup

    def save_soup(self) -> None:
        "Save the soup as a binary file."
        fn = f'{self.page_name}.pkl'
        with open(os.path.join(soups_path, fn), "wb") as f:
            pickle.dump(self.soup, f)

    def get_shortdescription(self) -> str:
        try:
            shortdescription = self.soup.find('div', class_='shortdescription').text
        except:
            shortdescription = 'no_shortdescription'
        return shortdescription

    def get_paragraphs_text(self) -> list:
        "Return the text of all paragraphs."
        paragraphs = []
        try:
            for p in self.soup.find_all('p'):
                paragraphs.append(p.text)
        except Exception as e:
            print(str(e))
        return paragraphs

    def save_paragraphs(self) -> None:
        "Save the list of paragraphs in a text file."
        fn = f'{self.page_name}.txt'
        fn_path = os.path.join(paragraphs_path, fn)
        with open(fn_path, "w") as f:
            f.write('\n'.join(self.paragraphs))

    def get_internal_page_names(self) -> list:
        """
        Extract all unique links from the page's content.
        Specifically, get all hrefs from <a> tags in <p> elements.
        """
        # List of characters or words to ignore when collecting page names
        exclude = ['#', '%', ':', '=', 'File:', 'Help:', 'List_of']
        hrefs = set()
        for p in self.soup.find_all('p'):
            for a in p.find_all('a'):
                try:
                    href = a.get('href')
                    if href.startswith('.') and not any(e in href for e in exclude):
                        hrefs.add(href[2:])
                except AttributeError:
                    continue
        return list(hrefs)


# def find_page_years(page_name: str) -> list:
#     soup = get_soup(page_name)
#     years = []
#     try:
#         for p in soup.find_all('p'):
#             p_text = p.text
#             # Find all 4 digit numbers in the text, filter to years between 1900 and 2025
#             matches = re.findall(r'\b(19[0-9]{2}|20[0-2][0-9]|2025)\b', p_text)
#             years.extend(matches)
#     except Exception as e:
#         print(str(e))
#     return years


# def find_page_persons(page_name: str) -> list:
#     labels = ["Person"]
#     soup = get_soup(page_name)
#     persons = []
#     try:
#         for p in soup.find_all('p'):
#             p_text = p.text
#             entities = model.predict_entities(p_text, labels, threshold=0.5)
#             for entity in entities:
#                 persons.append(entity["text"])
#     except Exception as e:
#         print(str(e))
#     return persons


