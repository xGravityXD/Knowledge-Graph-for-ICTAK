
import networkx as nx
from pyvis.network import Network

def to_pyvis_html(G: nx.DiGraph, output_html: str = "kg_result.html"):
    net = Network(height="750px", width="100%", bgcolor="#111111", font_color="white", directed=True)

    color_map = {
        "Course": "#FFA500",
        "Module": "#87CEFA",
        "Trainer": "#98FB98",
        "Student": "#FFC0CB",
        "Skill": "#E6E6FA"
    }

    for node, attrs in G.nodes(data=True):
        ntype = attrs.get("type", "Other")
        color = color_map.get(ntype, "#BBBBBB")
        title = f"{node}<br><i>{ntype}</i>"
        net.add_node(node, label=node, color=color, title=title)

    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("relation", "")
        net.add_edge(u, v, label=rel, title=rel, arrows="to")

    net.show(output_html)
    return output_html
