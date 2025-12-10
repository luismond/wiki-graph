
import pandas as pd
import networkx as nx
from pyvis.network import Network
import random


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
