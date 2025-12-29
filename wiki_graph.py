import random
from random import shuffle
import requests
import bs4
import pandas as pd
import numpy as np
import torch
import networkx as nx
from pyvis.network import Network
from sentence_transformers import SentenceTransformer
from dotenv import dotenv_values
from __init__ import logger, config
import db_utils as db


# Configuration
DB_NAME = config["DB_NAME"]
SEED_PAGE_NAME = config["SEED_PAGE_NAME"]
SIM_THRESHOLD = config["SIM_THRESHOLD"]
LANG_CODES = config["LANG_CODES"]
SBERT_MODEL_NAME = config["SBERT_MODEL_NAME"]


# Wikipedia access data
env_vars = {**dotenv_values()}
ACCESS_TOKEN = env_vars["ACCESS_TOKEN"]
APP_NAME = env_vars["APP_NAME"]
EMAIL = env_vars["EMAIL"]
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': f'{APP_NAME} ({EMAIL})'
    }


# SBERT model
MODEL = SentenceTransformer(SBERT_MODEL_NAME)


class CorpusManager:
    """
    The CorpusManager builds and manages the Wikipedia paragraph corpus
    from the database. It can load paragraphs and metadata,
    convert to a dataframe suitable for downstream processing,
    and keep track of corpus and embedding arrays.

    Key responsibilities:
        - Build the paragraph-level corpus from existing pages and paragraphs
          in the DB.
        - Load and access the corpus as structured data.
        - Prepare/coordinate corpus embeddings.
        - Provide convenient access to the main corpus and its properties.
        - Provide access to vector similarity and clustering functions.

    - sim_threshold (float): Minimum similarity score for included pages.
    - corpus: List of (page_id, page_name, text, position) tuples.
    - corpus_embedding: Numpy array of embeddings for each paragraph.
    - df: DataFrame view of the corpus.

    Usage:
        cm = CorpusManager()
        df = cm.df
        corpus_embedding = cm.corpus_embedding
    """
    def __init__(self):
        self.sim_threshold = SIM_THRESHOLD
        self.lang_codes = LANG_CODES
        self.corpus = None
        self.corpus_embedding = None
        self.df = None

    def load(self):
        """Initialize the module, build the corpus and load the vectors."""
        self._build()
        self.corpus = self._read()
        self.df = self._to_df()
        self._load_corpus_embedding()
        assert self.df.shape[0] == self.corpus_embedding.shape[0]

    def _read(self):
        corpus = db.get_paragraph_corpus()
        return corpus

    def _load_corpus_embedding(self):
        """
        Load all paragraph embeddings from the database
        and stack them into a numpy array.

        This method fetches the binary embeddings from the `embedding` column
        in the `paragraph_corpus` table, converts each to a float32 np array,
        and stacks them vertically to produce a 2D array.

        Sets:
            self.corpus_embedding (np.ndarray):
                An array of shape (num_paragraphs, embedding_dim).
        """
        embeddings = db.get_paragraph_embeddings()
        self.corpus_embedding = np.vstack(
            [np.frombuffer(e[0], dtype=np.float32) for e in embeddings]
            )
        logger.info('Loaded embeddings.')

    def _build(self):
        """
        Get the pages with sim_threshold >= self.sim_threshold
        and not in the paragraph_corpus table.
        For each page, create a WikiPage object and save it to the database.
        """
        logger.info('Building corpus...')

        pages = []
        for lang_code in self.lang_codes:
            pages_ = db.get_pages_data(self.sim_threshold, lang_code)
            for p in pages_:
                pages.append(p)

        corpus = self._read()
        pc_page_ids = set(i[1] for i in corpus)

        n = 0
        for page_id, page_name, lang_code, _ in pages:
            if page_id in pc_page_ids:
                continue
            wp = WikiPage(page_name, lang_code=lang_code)
            paragraphs = wp.paragraphs
            if len(paragraphs) == 0:
                continue
            for position, paragraph in enumerate(paragraphs):
                embedding = MODEL.encode(paragraph)
                embedding = np.array(embedding, dtype=np.float32).tobytes()
                db.insert_paragraph(page_id, paragraph, embedding, position)
            n += 1
        logger.info(f'Added {n} pages to corpus')

    def _to_df(self):
        df = pd.DataFrame(self.corpus)
        df.columns = [
            'paragraph_id', 'page_id', 'page_name',
            'text', 'position', 'lang_code']
        logger.info(f'Converted corpus to dataframe with shape {df.shape}')
        return df

    def _similarity_search(self, query: str, top_k_min: int=100) -> list:
        """Given a query, retrieve similar corpus rows."""
        # todo: add lang code parameter
        # embeddings
        corpus_embeddings = self.corpus_embedding
        query_embedding = MODEL.encode_query(query)

        # similarity scores
        similarity_scores = MODEL.similarity(query_embedding,
                                             corpus_embeddings)[0]
        top_k = min(top_k_min, len(self.df))
        scores, indices = torch.topk(similarity_scores, k=top_k)

        # similar rows
        rows = []
        for score, idx in zip(scores, indices):
            row = self.df.iloc[int(idx)]
            row['score'] = float(score)
            rows.append(row)
        logger.info(f'Returned {len(rows)} rows')
        return rows

    def similarity_by_paragraphs(
            self,
            query: str,
            top_k_min: int=100
            ) -> pd.DataFrame:
        """
        Retrieve similar rows, convert to df and sort by descending similarity.
        """
        rows = self._similarity_search(query=query, top_k_min=top_k_min)
        df = pd.DataFrame(rows).reset_index(drop=True)
        df = df.sort_values(by='score', ascending=False)
        logger.info(f'Returned {len(df)} paragraphs')
        return df

    def similarity_by_pages(
            self,
            query: str,
            top_k_min: int=100
            ) -> pd.DataFrame:
        "Group by page name and calculate paragraph similarity average."
        df = self.similarity_by_paragraphs(query=query, top_k_min=top_k_min)
        dfg = df.groupby('page_name', as_index=False)['score'].mean()
        dfg = dfg.sort_values(by='score', ascending=False)
        logger.info(f'Returned {len(dfg)} pages')
        return dfg


class CorpusBitexts:
    """Manage access to parallel (bitext) corpora for multiple languages."""
    def __init__(self):
        self.lang_codes = LANG_CODES
        self.df = None
        self.load()

    def load(self):
        self.df = self.get_bitext_corpus()
        self.len = len(self.df)
        self.word_count = self.get_word_count()
        logger.info(f'Loaded corpus bitexts with {self.len} rows')
        logger.info(f'Counted {self.word_count} corpus bitext words')

    @staticmethod
    def get_bitext(tgt_lang) -> pd.DataFrame:
        """
        Retrieve aligned bitext data for the specified target language.

        Args:
            tgt_lang (str): Target language code (e.g., 'fr', 'de', etc.)

        Returns:
            pd.DataFrame: DataFrame with columns -
                'page_name', 'page_id', 'autonym', 'autonym_page_id',
                'lang_code', 'src_text', 'tgt_text'

        The DataFrame contains matched paragraph texts in English and their
        corresponding autonym paragraphs in the target language.
        Each row corresponds to an aligned pair based on cross-lingual
        Wikipedia autonyms data.
        """
        autonyms_data = db.read_autonyms_data(tgt_lang)
        df = pd.DataFrame(autonyms_data)
        df.columns = ['page_name', 'page_id', 'autonym',
                      'autonym_page_id', 'lang_code']
        df['src_text'] = df['page_id'].apply(db.get_paragraphs_by_page_id)
        df['tgt_text'] = df['autonym_page_id'].apply(db.get_paragraphs_by_page_id)
        df = df.dropna()
        df = df.reset_index(drop=True)
        return df

    def get_bitext_corpus(self) -> pd.DataFrame:
        """
        Collect aligned bitext dataframes for all target languages
        in the corpus, concatenate them into a single DataFrame,
        and return the combined bitext corpus.

        Returns:
            pd.DataFrame: DataFrame containing aligned bitext pairs
            from all languages in 'lang_codes' except for English.
        """
        dfs = []
        for lang_code in self.lang_codes:
            if lang_code == 'en':
                continue
            df_ = self.get_bitext(lang_code)
            dfs.append(df_)
        df = pd.concat(dfs)
        df = df.reset_index(drop=True)
        return df

    def get_word_count(self) -> int:
        """
        Calculates the total number of words in both the source ('src_text')
        and target ('tgt_text') text columns of the DataFrame.

        Returns:
            int: The total count of words in both columns.
        """
        word_count = 0
        for i in self.df['src_text'].tolist():
            for _ in i.split():
                word_count += 1
        for i in self.df['tgt_text'].tolist():
            for _ in i.split():
                word_count += 1
        return word_count


class Crawler:
    def __init__(
        self,
        lang_code: str = 'en',
        max_pages: int = 50,
        max_new_pages: int = 50
        ):
        self.sim_threshold = SIM_THRESHOLD
        self.seed_page_name = SEED_PAGE_NAME
        self.max_pages = max_pages
        self.max_new_pages = max_new_pages
        self.lang_code = lang_code
        self.lang_codes = LANG_CODES
        self.autonym_lang_codes = None
        self.load()

    def set_autonym_lang_codes(self):
        self.autonym_lang_codes = [l for l in self.lang_codes \
                                   if l != self.lang_code]
        logger.info(f'Autonym lang codes: {self.autonym_lang_codes}')

    def load(self):
        """
        Initialize crawler with the seed page.

        - Save the page name.
        - Encode the seed paragraphs (todo: save them to vector db)
        """
        wp = WikiPage(self.seed_page_name, lang_code=self.lang_code)
        wp.save_page_name(sim_score=1.0)
        self.seed_paragraphs = wp.paragraphs
        self.seed_embedding = self.get_seed_embedding()
        self.set_autonym_lang_codes()
        logger.info(f'Loaded seed paragraphs from {self.seed_page_name}')

    def get_seed_embedding(self) -> np.ndarray:
        """
        Encode the seed paragraphs.
        This seed embedding will be used to determine the similarity
        of the new crawled pages.
        """
        seed_embedding = MODEL.encode(' '.join(self.seed_paragraphs))
        return seed_embedding

    def get_page_similarity_score(self, paragraphs: list) -> float:
        """
        Given a list of paragraphs, encode them and calculate
        their similarity against the seed.
        Args:
            paragraphs (list): A list of paragraphs.
        Returns:
            float: The similarity score between the paragraphs
            and the seed embedding.
        """
        paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
        sim_score = float(MODEL.similarity(paragraphs_embedding,
                                           self.seed_embedding)[0])
        return sim_score

    def process_new_page(self, page_name):
        """
        Process a new Wikipedia page name: fetch the page,
        compute similarity score, save its metadata to the database.

        Args:
            page_name (str): The name of the new Wikipedia page to process.
        """
        wp_new = WikiPage(page_name, lang_code=self.lang_code)
        sim_score = self.get_page_similarity_score(wp_new.paragraphs)
        wp_new.save_page_name(sim_score)

    def crawl(self):
        logger.info(f'Crawling pages with similarity threshold '
                    f'{self.sim_threshold}')
        self.crawl_source_lang_pages()
        self.crawl_autonym_pages()
        logger.info('Crawling complete')

    def crawl_source_lang_pages(self):
        """
        Crawl Wikipedia pages based on a similarity threshold.
        - For each page name from DB, extract internal Wikipedia links
        (<a> inside <p> tags).
        - For every internal link not already saved, process it as a new page
        (fetch the content, compute similarity, save metadata).
        """
        page_data = db.get_pages_data(self.sim_threshold, self.lang_code)
        page_names = [p[1] for p in page_data]
        shuffle(page_data)
        visited = set()
        for _, page_name, _, _ in page_data[:self.max_pages]:
            wp = WikiPage(page_name=page_name, lang_code=self.lang_code)
            new_page_names = wp.get_internal_page_names()
            shuffle(new_page_names)
            for new_page_name in new_page_names[:self.max_new_pages]:
                if new_page_name in list(visited) + page_names:
                    continue
                self.process_new_page(new_page_name)
                visited.add(new_page_name)

    def crawl_autonym_pages(self):
        """Populate the page_autonyms table and save autonym pages."""
        logger.info('populate_autonyms_table...')
        unsaved_pages = db.get_unsaved_autonym_page_ids(self.lang_code,
                                                        self.sim_threshold)
        n = 0
        for page_id, page_name in unsaved_pages:
            wp = WikiPage(page_name, self.lang_code)
            languages = wp.get_languages()
            if len(languages) == 0:
                continue
            for lang in languages:
                if not isinstance(lang, dict):
                    continue
                autonym = lang['key']
                lang_code = lang['code']
                if lang_code in self.autonym_lang_codes:
                    wp_x = WikiPage(page_name=autonym, lang_code=lang_code)
                    if len(wp_x.paragraphs) == 0:
                        continue
                    sim_score = self.get_page_similarity_score(wp_x.paragraphs)
                    wp_x.save_page_name(sim_score)
                    autonym_page_id = wp_x.page_id
                    db.insert_autonym(page_id, autonym,
                                      autonym_page_id, lang_code)
                    n += 1
        logger.info(f'Saved {n} autonyms')


class WikiPage:
    """
    Represents a single Wikipedia page.

    Includes methods to extract data and save it to the DB, such as
    page name, description, paragraph text, internal links and languages.

    """
    def __init__(self, page_name: str, lang_code: str):
        self.page_name = page_name
        self.lang_code = lang_code
        self.soup = None
        self.paragraphs = None
        self.shortdescription = None
        self.url = None
        self.page_id = None
        self.load()

    def load(self):
        """Get the page's url, download the soup and extract the paragraphs."""
        self.url = self.get_html_url()
        self.soup = self.download_soup()
        self.paragraphs = self.get_paragraphs_text()
        self.shortdescription = self.get_shortdescription()

    def __repr__(self):
        return f"<WikiPage {self.page_name}>"

    def get_html_url(self):
        """Format the URL with the language code and page name."""
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
        """
        Save the page metadata in the pages table and set the page id.
        """
        self.page_id = db.insert_page_metadata(self.page_name, self.lang_code,
                                               self.url, sim_score)

    def get_shortdescription(self) -> str:
        """Extract the short description."""
        try:
            shortdescr = self.soup.find('div', class_='shortdescription').text
        except AttributeError:
            shortdescr = 'no_shortdescription'
        return shortdescr

    def get_paragraphs_text(self) -> list:
        """
        Return the text of all paragraphs.

        Constraints: minimum words: 5. Alphabetic characters ratio: 75%.
        """

        def get_alpha_ratio(string: str) -> float:
            """Calculate the ratio of alphabetic characters in a string."""
            alpha_n = [ch for ch in string if ch.isalpha()]
            alpha_ratio = len(alpha_n) / len(string)
            return alpha_ratio

        paragraphs = []
        for p in self.soup.find_all('p'):
            p_text = p.text
            if len(p_text.split()) > 5 and get_alpha_ratio(p_text) > .75:
                paragraphs.append(p_text)
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
                    if href.startswith('.') \
                        and not any(e in href for e in exclude):
                        hrefs.add(href[2:])
                except AttributeError:
                    continue
        return list(hrefs)

    def get_languages(self) -> list:
        """
        Get a list of languages available for the page.
        Each language is a dictionary, for example:

        {'code': 'de', 'name': 'German', 'key': 'Erde', 'title': 'Erde'}

        Refer to: https://api.wikimedia.org/wiki/Core_REST_API/
                  Reference/Pages/Get_languages
        """
        url = (
            f'https://api.wikimedia.org/core/v1/wikipedia/{self.lang_code}'
            f'/page/{self.page_name}/links/language'
        )
        response = requests.get(url, headers=HEADERS, timeout=180)
        languages = response.json()
        return languages


class PagesGraph:
    """
    Represents a graph of the linked pages in the corpus.

    Implements methods to extract and save internal page links,
    build and filter the graph data, and visualize the graph.
    """
    def __init__(
            self,
            lang_code: str = 'en',
            sim_threshold: float = SIM_THRESHOLD
            ):
        self.lang_code = lang_code
        self.lang_codes = LANG_CODES
        self.sim_threshold = sim_threshold

    def load(self):
        self.build_page_links()
        dfr = self.read_page_links()
        dfx = self._filter(dfr)
        self.draw_graph(dfx)

    def build_page_links(self)-> pd.DataFrame:
        """Use the page names in page table to build the page_links data."""
        logger.info('Building page_links corpus...')
        pages = db.get_pages_data(self.sim_threshold, self.lang_code)
        page_id_dict = {name: id_ for id_, name, _, _ in pages}

        links_page_ids = db.get_page_links_page_ids()
        n = 0
        for page_id, page_name, _, _ in pages:
            if page_id in links_page_ids:
                continue
            wp = WikiPage(page_name, self.lang_code)
            new_page_names = wp.get_internal_page_names()
            for new_page_name in new_page_names:
                if new_page_name not in page_id_dict:
                    continue
                target_page_id = page_id_dict[new_page_name]
                db.insert_page_link(page_id, target_page_id)
                n += 1
        logger.info(f'Added {n} page_links')

    def read_page_links(self) -> pd.DataFrame:
        """Read the page_links data."""
        page_links = db.get_page_links_data(self.lang_code)
        columns = [
            's_page_id', 's_page_name', 's_page_sim_score',
            't_page_id', 't_page_name'
            ]
        df = pd.DataFrame(page_links, columns=columns)
        return df

    def _filter(
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
        df = df.drop(columns=['s_page_id', 't_page_id'])
        df.columns = ['source', 'sim_score', 'target']
        df['sim_score'] = df['sim_score'].astype(float)
        df['target_freq'] = df['target'].map(df['target'].value_counts())
        df = df.sort_values(by='target_freq', ascending=False)
        df = df[df['target_freq'] > freq_min]
        if groupby_source:
            df = pd.concat([b[:group_size] for (_, b) in df.groupby('source')])
        df = df[df['sim_score'] >= min_sim_score]
        df = df[:max_edges]
        filter_params = (
            f'freq_min={freq_min}, groupby_source={groupby_source}, '
            f'group_size={group_size}, max_edges={max_edges}'
            )
        logger.info(
            f'Returned filtered data with shape {df.shape}\n'
            f'Filter params: {filter_params}'
            )
        return df

    def build_graph(self, df) -> nx.Graph:
        # rd = pd.read_csv('data/csv/role_attrs.csv')
        # role_colors = dict(zip(rd['role'], rd['color']))
        # role_types = dict(zip(rd['role'], rd['type']))

        #df['source_color'] = df['source_role'].apply(role_colors.get)
        #df['target_color'] = df['target_role'].apply(role_colors.get)
        #df['source_type'] = df['source_role'].apply(role_types.get)
        #df['target_type'] = df['target_role'].apply(role_types.get)

        #df = df[df['source_type'].apply(lambda s: s not in {'media'})]
        #df = df[df['target_type'].apply(lambda s: s not in {'media'})]
        #df = apply_role_attrs(df)
        G = nx.Graph()

        random_html_colors = self.get_random_html_colors()

        # Add nodes with attributes
        for _, row in df.iterrows():
            source, target = row["source"], row["target"]
            source_color = random.choice(random_html_colors)
            #source_color = row.get("source_color", "gray")
            #source_role = row.get("source_role", "tbd")
            G.add_node(source, color=source_color)


            target_color = random.choice(random_html_colors)
            #target_role = row.get("target_role", "tbd")
            G.add_node(target, color=target_color)
            #G.add_node(target, role=target_role, title=target_role)

            # Add edges with attributes
            attrs = {k: row[k] for k in df.columns if k in ("edge_rank", "year")}
            G.add_edge(source, target, **attrs, relationship_list=[attrs.get("relationship", "")])
            if G.has_edge(source, target):
                G[source][target]["title"] = row.get("relationship", "")
        return G

    def draw_graph(self, df) -> None:
        net = Network(
            height="1800px",
            width="100%",
            notebook=False,
            neighborhood_highlight=False,
            select_menu=False,
            filter_menu=True
            )

        G = self.build_graph(df)
        net.from_nx(G)
        net.repulsion(node_distance=150)
        net.write_html("network_graph.html", open_browser=False)
        logger.info('graph completed')

    @staticmethod
    def get_random_html_colors():
        return [
            "#FF5733",  # Orange Red
            "#33FF57",  # Spring Green
            "#3357FF",  # Royal Blue
            "#FF33A1",  # Pink
            "#A133FF",  # Purple
            "#33FFF6",  # Aqua
            "#FFD433",  # Gold
            "#FF8333",  # Pumpkin
            "#33FF83",  # Mint
            "#A1FF33",  # Lime
            "#FF3333",  # Red
            "#33A1FF",  # Sky Blue
            "#D433FF",  # Orchid
            "#FF33D4",  # Hot Pink
            "#33FFD4",  # Turquoise
            "#87FF33",  # Light Green
            "#FF3387",  # Rose
            "#33D4FF",  # Baby Blue
            "#F6FF33",  # Light Yellow
            "#3387FF",  # Dodger Blue
        ]
