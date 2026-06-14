import networkx as nx

def canonicalized_logical_equivalence(g1: nx.DiGraph, g2: nx.DiGraph) -> bool:
    """
    Checks graph isomorphism under canonicalization.
    Assumes canonicalization (variable renaming, predicate ordering, etc.) already applied.
    """

    def node_match(a, b):
        return a.get("type") == b.get("type") and a.get("label") == b.get("label")

    def edge_match(a, b):
        return a.get("type") == b.get("type") and a.get("role") == b.get("role")

    return nx.is_isomorphic(g1, g2, node_match=node_match, edge_match=edge_match)


def equivalence_score(g1: nx.DiGraph, g2: nx.DiGraph) -> float:
    """
    Returns 1.0 if canonicalized graphs are logically equivalent, else 0.0.
    """
    return 1.0 if canonicalized_logical_equivalence(g1, g2) else 0.0