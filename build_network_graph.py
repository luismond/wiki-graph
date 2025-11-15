# build_network_graph.py
#
# Usage:
#   python build_network_graph.py relationship_graph_template.csv
# Produces:
#   - network_graph.png           (basic visualization)

import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from pyvis.network import Network

def load_attributes():
    df = pd.read_csv('node_attributes.csv')
    df = df.fillna('')
    df.index = df['node']
    ad = df.to_dict(orient='index')
    return ad

def load_edges(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # Coerce numeric columns if present
    if "weight" in df.columns:
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(1).astype(float)
    # Normalize whitespace
    for col in ["source", "target", "relationship", "edge_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    ad = load_attributes()
    df['source_color'] = df['source'].apply(lambda x: ad.get(x)['color'])
    return df

def build_graph(df: pd.DataFrame) -> nx.Graph:
    # Choose directed or undirected: toggle here if you need directionality.
    # For now, we treat the relationships as undirected.
    G = nx.Graph()
    # Add edges with attributes
    for _, row in df.iterrows():
        s, t = row["source"], row["target"]
        
        G.add_node(s, color=row.get("source_color", "gray"))
        #G.add_node(t, color=row.get("target_color", "gray"))

        attrs = {k: row[k] for k in df.columns if k not in ("source", "target")}
        # Combine parallel edges by accumulating weight
        if G.has_edge(s, t):
            G[s][t]["weight"] = G[s][t].get("weight", 1) + float(attrs.get("weight", 1))
            # Optionally track all relationship labels
            rels = G[s][t].get("relationship_list", [])
            rels.append(attrs.get("relationship", ""))
            G[s][t]["relationship_list"] = rels
        else:
            G.add_edge(s, t, **attrs, relationship_list=[attrs.get("relationship", "")])
    return G


def draw_graph_pyvis(G: nx.Graph) -> None:
    net = Network(
        height="1200px",
        width="100%",
        notebook=False,
        neighborhood_highlight=True,
        select_menu=True,
        filter_menu=True
        )
    net.from_nx(G)
    net.show("network_graph.html", notebook=False)


def main():
    csv_path = Path(sys.argv[1])
    edges = load_edges(csv_path)
    G = build_graph(edges)
    draw_graph_pyvis(G)


if __name__ == "__main__":
    main()



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


# def draw_graph(G: nx.Graph) -> None:
#     # Simple force-directed layout
#     pos = nx.spring_layout(G, seed=42, k=None, scale=2, method='energy')

#     # Node sizes scaled by degree
#     degrees = dict(G.degree())
#     sizes = [350 + 150 * degrees[n] for n in G.nodes()]
#     colors = [G.nodes[n].get("color", "gray") for n in G.nodes()]

#     nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, alpha=0.9)

#     edge_colors = [G[u][v].get("edge_color", "gray") for u, v in G.edges()]
#     edge_widths = [G[u][v].get("weight", 1) for u, v in G.edges()]
#     nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, alpha=0.5)

#     nx.draw_networkx_labels(G, pos, font_size=12)

#     plt.figure(figsize=(26, 14), facecolor='#D3D3D3')
#     plt.axis("off")
#     plt.tight_layout()
#     plt.savefig("network_graph.png", dpi=450)
#     plt.close()
