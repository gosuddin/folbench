import networkx as nx
import matplotlib.pyplot as plt


def visualize_fol_graph(
 g: nx.DiGraph,
 title: str = "FOLBench Graph",
 figsize=(10, 8),
 node_size=1800,
 font_size=10,
):
    """
    Visualizes a FOLBench graph with node types, labels, and edge types.
    Works with the FOLBench graph schema:
    node['type'] ∈ {predicate, variable, constant, quantifier, connective}
    node['label'] = string
    node['is_root'] = optional bool
    edge['type'] ∈ {arg, binding, scope, logical}
    edge['role'] = optional (for arg edges)
    """

    # ---- Node styling by type ----
    type_to_color = {
    "predicate": "#4C72B0",
    "variable": "#55A868",
    "constant": "#C44E52",
    "quantifier": "#8172B2",
    "connective": "#CCB974",
    }

    type_to_shape = {
    "predicate": "o",
    "variable": "s",
    "constant": "D",
    "quantifier": "^",
    "connective": "v",
    }

    # ---- Layout ----
    pos = nx.spring_layout(g, seed=42)

    plt.figure(figsize=figsize)
    plt.title(title, fontsize=14)

    # ---- Draw nodes by type ----
    for ntype in type_to_color:
        nodes_of_type = [n for n, d in g.nodes(data=True) if d.get("type") == ntype]
        if not nodes_of_type:
            continue

        nx.draw_networkx_nodes(
            g,
            pos,
            nodelist=nodes_of_type,
            node_color=type_to_color[ntype],
            node_shape=type_to_shape[ntype],
            node_size=node_size,
            alpha=0.9,
        )

    # ---- Node labels ----
    node_labels = {
        n: f"{d.get('label')}"
        + ("\n(ROOT)" if d.get("is_root") else "")
        for n, d in g.nodes(data=True)
    }
    nx.draw_networkx_labels(g, pos, labels=node_labels, font_size=font_size)

    # ---- Edge labels ----
    edge_labels = {}
    for u, v, d in g.edges(data=True):
        etype = d.get("type")
        if etype == "arg":
            label = f"arg:{d.get('role')}"
        else:
            label = etype
        edge_labels[(u, v)] = label

    nx.draw_networkx_edges(g, pos, arrows=True, arrowstyle="-|>", arrowsize=20)
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=font_size)

    plt.axis("off")
    plt.tight_layout()
    plt.show()