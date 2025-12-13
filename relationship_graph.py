"""Utils to build and visualize page relationships."""

import os
import re
import random
import pandas as pd
import networkx as nx
from pyvis.network import Network
from corpus_manager import CorpusManager
from wiki_page import WikiPage
import sqlite3
from __init__ import current_datetime_str, logger



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
    df['relationship'] = 'co_occurs_with'
    G = nx.Graph()
    
    random_html_colors = get_random_html_colors()

    # Add nodes with attributes
    for _, row in df.iterrows():
        source, target = row["source"], row["target"]
        source_color = random.choice(random_html_colors)
        #source_color = row.get("source_color", "gray")
        #source_role = row.get("source_role", "tbd")
        G.add_node(source, color=source_color)
        #G.add_node(target, bin=row.get("bin", 10))
        #G.add_node(source, bin=row.get("bin", 10))

        target_color = random.choice(random_html_colors)
        #target_role = row.get("target_role", "tbd")
        G.add_node(target, color=target_color)
        #G.add_node(target, role=target_role, title=target_role)

        # Add edges with attributes
        attrs = {k: row[k] for k in df.columns if k in ("edge_rank", "year")}
        G.add_edge(source, target, **attrs, relationship_list=[attrs.get("relationship", "")])
        if G.has_edge(source, target):
            G[source][target]["title"] = row.get("relationship", "")
            # G[source][target]["bin"] = row.get("bin", 10)
    return G


def draw_graph_pyvis(df) -> None:
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


def compute_metrics(G: nx.Graph) -> pd.DataFrame:
    deg = dict(G.degree())
    btwn = nx.betweenness_centrality(G) if len(G) > 2 else {n: 0 for n in G.nodes()}
    # Community detection (greedy modularity)
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        comms = list(greedy_modularity_communities(G)) if len(G) > 0 else []
        node_to_comm = {}
        for cid, comm in enumerate(comms):
            for n in comm:
                node_to_comm[n] = cid
    except Exception:
        node_to_comm = {n: -1 for n in G.nodes()}

    df = pd.DataFrame({
        "node": list(G.nodes()),
        "degree": [deg[n] for n in G.nodes()],
        "betweenness": [btwn[n] for n in G.nodes()],
        "community": [node_to_comm.get(n, -1) for n in G.nodes()]
    }).sort_values(["community", "degree"], ascending=[True, False])
    return df


class RelationshipBuilder:
    """
    Reads the stored page objects and
    builds a dataframe `relationships` with these columns:
        - id (PK)
        - source_page_id (FK)
        - target_id (FK)
        - relationship_type
            - internal_link (from WikiPage.get_internal_page_names)
            - year          (find_page_years)
            - person        (todo)
    """
    def __init__(self):
        self.data = None
        self.load()

    def load(self):
        self._build()
        self.data = self._read()

    def _build(self)-> pd.DataFrame:
        """Use the page names in page table to build the relationship data."""
        logger.info(f'Building relationship corpus...')
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("SELECT id, name, sim_score FROM pages")

        pages = cur.fetchall()
        cur.execute("SELECT source_page_id FROM relationships")
        rel_page_ids = cur.fetchall()  # list of page_ids stored in relationships table
        rel_page_ids = set([p[0] for p in rel_page_ids])
        logger.info(f'{len(rel_page_ids)} page_ids in relationships table')

        # issue: if source_page_id exists, how to save subsequent, different relations?
        n = 0
        for page_id, page_name, sim_score in pages:
            if page_id not in rel_page_ids and sim_score >= .4:
                wp = WikiPage(page_name)
                new_page_names = wp.get_internal_page_names()
                for new_page_name in new_page_names:
                    cur.execute(
                        "INSERT INTO relationships (source_page_id, target, target_type) VALUES (?, ?, ?)",
                        (page_id, new_page_name, 'internal_link')
                        )
                    conn.commit()
                    n += 1
                # years = self.find_page_years(page_name)  
                # if len(years) > 0:
                #     for year in years:
                #         rows.append((page_name, year, 'year'))
                # persons = find_page_persons(page_name)  
                # if len(persons) > 0:
                #     for person in persons:
                #         rows.append((page_name, person))
        logger.info(f'Added {n} relationships')
       

    def _read(self) -> pd.DataFrame:
        """Read the relationship data."""
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("""
            SELECT relationships.source_page_id, pages.name, relationships.target, relationships.target_type
            FROM relationships
            LEFT JOIN pages ON relationships.source_page_id = pages.id
        """)
        relationships = cur.fetchall()
        df = pd.DataFrame(relationships, columns=['source_page_id', 'source', 'target', 'target_type'])
        logger.info(f'Read {len(df)} relationships from relationships table')
        return df

    @staticmethod
    def find_page_years(page_name) -> list:
        """Find all 4 digit numbers in the text, filter to years between 1900 and 2025"""
        wp = WikiPage(page_name)
        years = []
        for p in wp.soup.find_all('p'):
            matches = re.findall(r'\b(19[0-9]{2}|20[0-2][0-9]|2025)\b', p.text)
            years.extend(matches)
        return years

    def _filter(
        self,
        freq_min=3,
        groupby_source=True,
        group_size=20,
        max_edges=500
        ):
        df = self.data
        df['target_freq'] = df['target'].map(df['target'].value_counts())
        df = df.sort_values(by='target_freq', ascending=False)
        df = df[df['target_freq'] > freq_min]
        if groupby_source:
            df = pd.concat([b[:group_size] for (_, b) in df.groupby('source')])
        df = df[:max_edges]
        filter_params = f'freq_min={freq_min}, groupby_source={groupby_source}, group_size={group_size}, max_edges={max_edges}'
        print(f'Returned filtered data with shape {df.shape}\nFilter params: {filter_params}')
        return df


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




# # Chunk target_freq unique values into 5 groups
# freq_values = np.sort(dfr['target_freq'].unique())
# bins = np.array_split(freq_values, 5)
# bins_dict = defaultdict()
# for i, b in enumerate(bins):
#     for freq in b:
#         bins_dict[int(freq)] = i
# dfr['bin'] = dfr['target_freq'].map(bins_dict)