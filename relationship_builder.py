"""Utils to build and visualize page relationships."""

import json
import pandas as pd
import sqlite3
from wiki_page import WikiPage
from __init__ import logger, DB_NAME


class RelationshipBuilder:
    """
    Reads the stored page objects and builds a dataframe `relationships` with these columns:
        - id (PK)
        - source_page_id (FK)
        - target_page_id (FK)
    """
    def __init__(self, sim_threshold: float = .45):
        self.sim_threshold = sim_threshold

    def get_pages(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name, sim_score FROM pages")
        pages = cur.fetchall()
        logger.info(f'{len(pages)} page_ids in pages table')
        return pages

    def build_page_links(self)-> pd.DataFrame:
        """Use the page names in page table to build the page_links data."""
        logger.info(f'Building page_links corpus...')
        pages = self.get_pages()
        page_id_dict = {name: id_ for id_, name, _ in pages}

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT source_page_id FROM page_links")
        links_page_ids = cur.fetchall()
        links_page_ids = set([p[0] for p in links_page_ids])
        logger.info(f'{len(links_page_ids)} page_ids in page_links table')

        n = 0
        for page_id, page_name, sim_score in pages:
            if page_id not in links_page_ids and sim_score >= self.sim_threshold:
                wp = WikiPage(page_name)
                new_page_names = wp.get_internal_page_names()
                for new_page_name in new_page_names:
                    if new_page_name not in page_id_dict:
                        continue
                    target_page_id = page_id_dict[new_page_name]
                    cur.execute(
                        "INSERT INTO page_links (source_page_id, target_page_id) VALUES (?, ?)",
                        (page_id, target_page_id)
                        )
                    conn.commit()
                    n += 1
        logger.info(f'Added {n} page_links')


    def build_page_langs(self)-> pd.DataFrame:
        """Use the page names in page table to populate the page_langs table."""
        logger.info(f'Building page_langs corpus...')
        pages = self.get_pages()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT page_id FROM page_langs")
        langs_page_ids = cur.fetchall()
        langs_page_ids = set([p[0] for p in langs_page_ids])
        logger.info(f'{len(langs_page_ids)} page_ids in page_langs table')

        n = 0
        for page_id, page_name, sim_score in pages:
            if page_id not in langs_page_ids and sim_score >= self.sim_threshold:
                wp = WikiPage(page_name)
                languages = wp.get_languages()
                if len(languages) == 0:
                    continue
                languages = json.dumps(languages)
                cur.execute(
                    "INSERT INTO page_langs (page_id, langs) VALUES (?, ?)",
                    (page_id, languages)
                    )
                conn.commit()
                n += 1
        logger.info(f'Added {n} page_langs')

    def read_page_links(self) -> pd.DataFrame:
        """Read the page_links data."""
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT page_links.source_page_id, source_pages.name, 
            page_links.target_page_id, target_pages.name, target_pages.sim_score
            FROM page_links
            LEFT JOIN pages AS source_pages ON page_links.source_page_id = source_pages.id
            LEFT JOIN pages AS target_pages ON page_links.target_page_id = target_pages.id
        """)
        page_links = cur.fetchall()
        columns = ['source_page_id', 'source', 'target_page_id', 'target', 'sim_score']
        df = pd.DataFrame(page_links, columns=columns)
        logger.info(f'Read {len(df)} page_links from page_links table')
        return df

    def read_page_langs(self) -> pd.DataFrame:
        """Read the page_langs data."""
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT page_langs.page_id, pages.name, page_langs.langs
            FROM page_langs
            LEFT JOIN pages ON page_langs.page_id = pages.id
        """)
        page_langs = cur.fetchall()
        page_langs = [(page_id, name, json.loads(langs)) for (page_id, name, langs) in page_langs]
        columns = ['page_id', 'name', 'langs']
        df = pd.DataFrame(page_langs, columns=columns)
        logger.info(f'Read {len(df)} page_links from page_links table')
        return df

    def filter(
        self,
        df,
        freq_min=3,
        groupby_source=True,
        group_size=20,
        max_edges=500,
        min_sim_score=.5
        ):
        """
        Filter the relationship dataframe according to several parameters.

        Args:
            freq_min (int): Minimum number of times a target must appear to be kept.
            groupby_source (bool): Whether to group results by source node.
            group_size (int): Number of edges to keep per source group if groupby_source is True.
            max_edges (int): Maximum number of edges to return after filtering.
            min_sim_score (float): Minimum similarity score threshold for included relationships.

        Returns:
            pd.DataFrame: Filtered relationship dataframe.
        """
        df['target_freq'] = df['target'].map(df['target'].value_counts())
        df = df.sort_values(by='target_freq', ascending=False)
        df = df[df['target_freq'] > freq_min]
        if groupby_source:
            df = pd.concat([b[:group_size] for (_, b) in df.groupby('source')])
        df = df[df['sim_score'] >= min_sim_score]
        df = df[:max_edges]
        filter_params = f'freq_min={freq_min}, groupby_source={groupby_source}, group_size={group_size}, max_edges={max_edges}'
        print(f'Returned filtered data with shape {df.shape}\nFilter params: {filter_params}')
        return df


# TODO:

# @staticmethod
# def find_page_years(page_name) -> list:
#     """Find all 4 digit numbers in the text, filter to years between 1900 and 2025"""
#     wp = WikiPage(page_name)
#     years = []
#     for p in wp.soup.find_all('p'):
#         matches = re.findall(r'\b(19[0-9]{2}|20[0-2][0-9]|2025)\b', p.text)
#         years.extend(matches)
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
