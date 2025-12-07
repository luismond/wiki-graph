# build_network_graph.py
#
# Usage:
#   python build_network_graph.py relationships.csv
# Produces:
#   - network_graph.html

# Spreadsheet structure and formulas:
#
# relationship_graph.sheets
#   relationships
#       source, source_role, relationship, target, target_role, year, url_title, url, source_rank
#   node_attrs
#       node, role, rank
#   role_colors
#       role, color
#
# =vlookup(A2, node_attrs!A:B, 2, FALSE)


import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from pyvis.network import Network
import random

def load_role_attrs():
    df = pd.read_csv('data/csv/role_attrs.csv')
    return df


def load_data(path: Path, max_edges) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.fillna('')
    df['relationship'] = 'co_occurs_with'
    print(len(df))
    df = df.sort_values(by='target_freq', ascending=False)
    df = df[:max_edges]#df[df['target_freq'] > 15]
    print(len(df))

    rd = load_role_attrs()
    role_colors = dict(zip(rd['role'], rd['color']))
    role_types = dict(zip(rd['role'], rd['type']))
  
    #df['source_color'] = df['source_role'].apply(role_colors.get)
    #df['target_color'] = df['target_role'].apply(role_colors.get)
    #df['source_type'] = df['source_role'].apply(role_types.get)
    #df['target_type'] = df['target_role'].apply(role_types.get)

    #df = df[df['source_type'].apply(lambda s: s not in {'media'})]
    #df = df[df['target_type'].apply(lambda s: s not in {'media'})]
    return df


def build_graph(csv_path, max_edges) -> nx.Graph:
    # Initialize graph
    df = load_data(csv_path, max_edges)
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in df.iterrows():
        source, target = row["source"], row["target"]

        random_html_colors = [
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

        source_color = random.choice(random_html_colors)
        #source_color = row.get("source_color", "gray")
        #source_role = row.get("source_role", "tbd")
        G.add_node(source, color=source_color)
        #G.add_node(source, role=source_role, title=source_role)

        #target_color = row.get("target_color", "gray")
        #target_role = row.get("target_role", "tbd")
        #G.add_node(target, color=target_color)
        #G.add_node(target, role=target_role, title=target_role)

        # Add edges with attributes
        attrs = {k: row[k] for k in df.columns if k in ("edge_rank", "year")}
        G.add_edge(source, target, **attrs, relationship_list=[attrs.get("relationship", "")])
        if G.has_edge(source, target):
            G[source][target]["title"] = row.get("relationship", "")
    return G


def draw_graph_pyvis(max_edges=700) -> None:
    net = Network(
        height="1400px",
        width="100%",
        notebook=False,
        neighborhood_highlight=True,
        select_menu=False,
        filter_menu=False
        )
    G = build_graph('data/csv/wiki_rels.csv', max_edges)
    net.from_nx(G)
    net.repulsion(node_distance=200)
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


def main():
    #csv_path = Path(sys.argv[1])
    #G = build_graph(csv_path, max_edges=900)
    draw_graph_pyvis()


if __name__ == "__main__":
    main()


