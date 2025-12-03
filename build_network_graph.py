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


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.fillna('')

    df = df[df['target_freq'] > 1]

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


def build_graph(df: pd.DataFrame) -> nx.Graph:
    # Initialize graph
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in df.iterrows():
        source, target = row["source"], row["target"]

        color_options = [
            "#FFB6C1",  # LightPink
            "#E6E6FA",  # Lavender
            "#FFFACD",  # LemonChiffon
            "#D1EEEE",  # LightCyan2
            "#E0FFFF",  # LightCyan
            "#F0FFF0",  # Honeydew
            "#F5FFFA",  # MintCream
            "#F0FFFF",  # Azure
            "#F5F5DC",  # Beige
            "#FAFAD2",  # LightGoldenrodYellow
            "#FFE4E1",  # MistyRose
            "#FDF5E6",  # OldLace
            "#FFF0F5",  # LavenderBlush
            "#FFF5EE",  # Seashell
            "#F8F8FF"   # GhostWhite
        ]

        source_color = random.choice(color_options)
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


def draw_graph_pyvis(G: nx.Graph) -> None:
    net = Network(
        height="1400px",
        width="100%",
        notebook=False,
        neighborhood_highlight=False,
        select_menu=True,
        filter_menu=True
        )
    net.from_nx(G)
    net.repulsion()
    net.write_html("network_graph.html", open_browser=False)


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
    csv_path = Path(sys.argv[1])
    data = load_data(csv_path)
    G = build_graph(data)
    draw_graph_pyvis(G)


if __name__ == "__main__":
    main()


