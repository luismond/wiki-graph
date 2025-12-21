"""
WikiPage class.

Represents a single Wikipedia page.

Includes methods to download, parse, and extract links and paragraphs.
Also, methods to save page data to the database.
"""

import requests
import bs4
import sqlite3
from __init__ import HEADERS, logger, DB_NAME, current_datetime_str


class WikiPage:
    def __init__(self, page_name: str, lang_code: str):
        self.page_name = page_name
        self.lang_code = lang_code
        self.soup = None
        self.paragraphs = []
        self.shortdescription = None
        self.url = None
        self.page_id = None
        self.load()

    def load(self):
        self.url = self.get_html_url()
        self.soup = self.download_soup()
        self.paragraphs = self.get_paragraphs_text()
        self.shortdescription = self.get_shortdescription()

    def __repr__(self):
        return f"<WikiPage {self.page_name}>"

    def get_html_url(self):
        return (
            f'https://api.wikimedia.org/core/v1/wikipedia/'
            f'{self.lang_code}/page/{self.page_name}/html'
        )

    def download_soup(self) -> bs4.BeautifulSoup:
        """"
        Request a Wikipedia url
        and return the parsed html page as a bs4 soup.
        """
        try:
            response = requests.get(self.url, headers=HEADERS, timeout=180)
            soup = bs4.BeautifulSoup(response.text, features="html.parser")
        except requests.exceptions.ConnectionError as e:
            logger.info(str(e))
        except requests.exceptions.ReadTimeout as e:
            logger.info(str(e))
        return soup

    def save_page_name(self, sim_score):
        """Save the page metadata in the pages table."""
        # todo: rename method to "save_page_metadata"
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
        "INSERT OR IGNORE INTO pages "
        "(name, lang_code, url, crawled_at, sim_score) VALUES (?, ?, ?, ?, ?)",
        (self.page_name, self.lang_code, self.url, current_datetime_str, sim_score)
        )
        self.page_id = cur.lastrowid
        conn.commit()
        
    def get_shortdescription(self) -> str:
        # todo: decide if remove or save it along the metadata
        try:
            shortdescription = self.soup.find('div', class_='shortdescription').text
        except:
            shortdescription = 'no_shortdescription'
        return shortdescription

    def get_paragraphs_text(self) -> list:
        "Return the text of all paragraphs."

        def get_alpha_ratio(string: str) -> float:
            """Calculate the ratio of alphabetic characters in a string."""
            alpha_n = [ch for ch in string if ch.isalpha()]
            alpha_ratio = len(alpha_n) / len(string)
            return alpha_ratio

        paragraphs = []
        try:
            for p in self.soup.find_all('p'):
                p_text = p.text
                if len(p_text.split()) > 5 and get_alpha_ratio(p_text) > .75:
                    paragraphs.append(p_text)
        except Exception as e:
            logger.error(str(e))
        return paragraphs

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

    def get_languages(self) -> list:
        """
        Get a list of dictionaries containing the code, name,
        key, and title of the page languages.

        Returns:
            A list of dictionaries. For example:
            [{'code': 'sv', 'name': 'svenska', 'key': 'Flygande_tefat', 'title': 'Flygande tefat'},
             {'code': 'th', 'name': 'ไทย', 'key': 'จานบิน', 'title': 'จานบิน'}]

        Refer to: https://api.wikimedia.org/wiki/Core_REST_API/Reference/Pages/Get_languages
        """
        url = (
            f'https://api.wikimedia.org/core/v1/wikipedia/{self.lang_code}'
            f'/page/{self.page_name}/links/language'
        )
        response = requests.get(url, headers=HEADERS, timeout=180)
        languages = response.json()
        return languages
