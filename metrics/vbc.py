import networkx as nx

def _binding_map(g: nx.DiGraph):
    """
    Returns a mapping: quantifier_node -> set of variable labels it binds.
    """
    bind = {}
    for u, v, d in g.edges(data=True):
        if d.get("type") == "binding":
            q_label = g.nodes[u].get("label")
            v_label = g.nodes[v].get("label")
            bind.setdefault(q_label, set()).add(v_label)
    return bind


def variable_binding_consistency(g_pred: nx.DiGraph, g_gold: nx.DiGraph) -> float:
    """
    VBC: measures how consistent variable binding is between predicted and gold graphs.
    Compares quantifier -> {variables} mappings by label.
    """
    b_pred = _binding_map(g_pred)
    b_gold = _binding_map(g_gold)

    if not b_pred and not b_gold:
        return 1.0
    if not b_gold:
        return 0.0

    matched = 0
    total = max(len(b_pred), len(b_gold))

    for q_label, vars_pred in b_pred.items():
        vars_gold = b_gold.get(q_label)
        if vars_gold is None:
            continue
        if vars_pred == vars_gold:
            matched += 1

    return matched / total if total > 0 else 0.0