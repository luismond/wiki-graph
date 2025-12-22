"""Utils to build and visualize page relationships."""

import sqlite3
import random
import pandas as pd
import networkx as nx
from pyvis.network import Network
from db_util import get_pages_data
from wiki_page import WikiPage
from __init__ import logger, DB_NAME, SIM_THRESHOLD


class RelationshipBuilder:
    def __init__(
            self,
            lang_code: str = 'en',
            sim_threshold: float = SIM_THRESHOLD
            ):
        self.lang_code = lang_code
        self.sim_threshold = sim_threshold

    def build_page_links(self)-> pd.DataFrame:
        """Use the page names in page table to build the page_links data."""
        logger.info('Building page_links corpus...')
        pages = get_pages_data(self.sim_threshold, self.lang_code)
        page_id_dict = {name: id_ for id_, name, _, _ in pages}

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT source_page_id FROM page_links")
        links_page_ids = cur.fetchall()
        links_page_ids = set(p[0] for p in links_page_ids)
        logger.info(f'{len(links_page_ids)} page_ids in page_links table')

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
                cur.execute(
                    "INSERT INTO page_links "
                    "(source_page_id, target_page_id) VALUES (?, ?)",
                    (page_id, target_page_id)
                    )
                conn.commit()
                n += 1
        logger.info(f'Added {n} page_links')

    def read_page_links(self) -> pd.DataFrame:
        """Read the page_links data."""
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT pl.source_page_id, s_pages.name, s_pages.sim_score,
            pl.target_page_id, t_pages.name
            FROM page_links AS pl
            LEFT JOIN pages AS s_pages ON pl.source_page_id = s_pages.id
            LEFT JOIN pages AS t_pages ON pl.target_page_id = t_pages.id
            WHERE s_pages.lang_code = ?
        """, (self.lang_code,)
        )
        page_links = cur.fetchall()
        columns = ['s_page_id', 's_page_name', 's_page_sim_score',
        't_page_id', 't_page_name']
        df = pd.DataFrame(page_links, columns=columns)
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
            'group_size={group_size}, max_edges={max_edges}'
            )
        print(
            f'Returned filtered data with shape {df.shape}\n'
            f'Filter params: {filter_params}'
            )
        return df


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


def apply_role_attrs(df):
    rd = pd.read_csv('data/csv/role_attrs.csv')
    role_colors = dict(zip(rd['role'], rd['color']))
    role_types = dict(zip(rd['role'], rd['type']))
  
    #df['source_color'] = df['source_role'].apply(role_colors.get)
    #df['target_color'] = df['target_role'].apply(role_colors.get)
    #df['source_type'] = df['source_role'].apply(role_types.get)
    #df['target_type'] = df['target_role'].apply(role_types.get)

    #df = df[df['source_type'].apply(lambda s: s not in {'media'})]
    #df = df[df['target_type'].apply(lambda s: s not in {'media'})]
    return df


def build_graph(df) -> nx.Graph:

    #df = apply_role_attrs(df)
    G = nx.Graph()
    
    random_html_colors = get_random_html_colors()

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


def draw_graph(df) -> None:
    net = Network(
        height="1800px",
        width="100%",
        notebook=False,
        neighborhood_highlight=False,
        select_menu=False,
        filter_menu=True
        )

    G = build_graph(df)
    net.from_nx(G)
    net.repulsion(node_distance=150)
    net.write_html("network_graph.html", open_browser=False)
    print('graph completed')


# def compute_metrics(G: nx.Graph) -> pd.DataFrame:
#     deg = dict(G.degree())
#     btwn = nx.betweenness_centrality(G) if len(G) > 2 else {n: 0 for n in G.nodes()}
#     # Community detection (greedy modularity)
#     try:
#         from networkx.algorithms.community import greedy_modularity_communities
#         comms = list(greedy_modularity_communities(G)) if len(G) > 0 else []
#         node_to_comm = {}
#         for cid, comm in enumerate(comms):
#             for n in comm:
#                 node_to_comm[n] = cid
#     except Exception:
#         node_to_comm = {n: -1 for n in G.nodes()}

#     df = pd.DataFrame({
#         "node": list(G.nodes()),
#         "degree": [deg[n] for n in G.nodes()],
#         "betweenness": [btwn[n] for n in G.nodes()],
#         "community": [node_to_comm.get(n, -1) for n in G.nodes()]
#     }).sort_values(["community", "degree"], ascending=[True, False])
#     return df

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

# from gliner import GLiNER
# model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
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
