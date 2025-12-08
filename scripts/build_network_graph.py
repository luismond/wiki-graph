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
    df = df.sort_values(by='target_freq', ascending=False)
    #df = df[df['target_freq'] >= 2]
    print(len(df))
    df = pd.concat([b[:20] for (_, b) in df.groupby('source')])
    print(df.head())
   
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


def build_graph(csv_path, max_edges) -> nx.Graph:
    # Initialize graph
    df = load_data(csv_path, max_edges)
    G = nx.Graph()
    
    random_html_colors = get_random_html_colors()

    # Add nodes with attributes
    for _, row in df.iterrows():
        source, target = row["source"], row["target"]
        source_color = random.choice(random_html_colors)
        #source_color = row.get("source_color", "gray")
        #source_role = row.get("source_role", "tbd")
        G.add_node(source, color=source_color)
        G.add_node(target, bin=row.get("target_freq", "1"))

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


def draw_graph_pyvis(max_edges=1000) -> None:
    net = Network(
        height="1400px",
        width="100%",
        notebook=False,
        neighborhood_highlight=True,
        select_menu=False,
        filter_menu=True
        )
    G = build_graph('data/csv/page_relationships.csv', max_edges)
    net.from_nx(G)
    net.repulsion(node_distance=200)
    net.write_html("network_graph.html", open_browser=False)
    print('graph completed')


def main():
    #csv_path = Path(sys.argv[1])
    #G = build_graph(csv_path, max_edges=900)
    draw_graph_pyvis()


if __name__ == "__main__":
    main()


