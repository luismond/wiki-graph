"""Utils to build and visualize page relationships."""

import os
import re
import random
from datetime import datetime
import pandas as pd
import networkx as nx
from pyvis.network import Network
from corpus_manager import CorpusManager
from wiki_page import WikiPage
from __init__ import DATA_PATH


current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')

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






def build_page_relationships(target='page'):
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the relevant data from each page name
            - targets can be one of these types:
                - internal link
                - year
                - person
        - "target_freq" -> int: the overall frequency value of the targets
    todo: define a database of page relationships
    """
    cm = CorpusManager()
    corpus = cm.corpus
    
    page_names = corpus['page_name'].tolist()[:100]
    print(f'Building relationships from {len(page_names)} pages...')
    
    rows = []
    for page_name in page_names:
        if target == 'page':
            wp = WikiPage(page_name)
            new_page_names = wp.get_internal_page_names()
            for new_page_name in new_page_names:
                rows.append((page_name, new_page_name))
        # if target == 'year':
        #     years = find_page_years(page_name)  
        #     if len(years) > 0:
        #         for year in years:
        #             rows.append((page_name, year))
        # if target == 'person':
        #     persons = find_page_persons(page_name)  
        #     if len(persons) > 0:
        #         for person in persons:
        #             rows.append((page_name, person))
            
    df = pd.DataFrame(rows)
    df.columns = ['source', 'target']
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    print(f'Built {len(df)} relationships')
    # save_page_relationships(df, target)
    return df


# def save_page_relationships(df, target):
#     fn = f'page_relationships_{target}_{current_datetime_str}.csv'
#     fp = os.path.join(DATA_PATH, fn)
#     df.to_csv(fp, index=False, sep=',')
#     print(f'{len(df)} relationships saved to {fp}')


# def read_page_relationships(target):
#     fn = f'page_relationships_{target}_{current_datetime_str}.csv'
#     fp = os.path.join(DATA_PATH, fn)
#     df = pd.read_csv(fp)
#     print(f'{len(df)} relationships read from {fp}')
#     return df


# def get_page_relationships(target):
#     fn = f'page_relationships_{target}_{current_datetime_str}.csv'
#     if fn in os.listdir(DATA_PATH):
#         df = read_page_relationships(target)
#     else:
#         df = build_page_relationships(target)
#     return df


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

# def filter_r(df):
#     #df = df[df['target'].apply(lambda s: s in top_pages)]
#     # df = df[df['target'].apply(lambda s: s in top_pages)]
#     max_edges = 750
#     df['relationship'] = 'co_occurs_with'
#     df = df.sort_values(by='target_freq', ascending=False)
#     df = df[df['target_freq'] > 2]
#     print(df.shape)
#     df = pd.concat([b[:20] for (_, b) in df.groupby('source')])
#     df = df[:max_edges]
#     print(df.shape)
#     return df