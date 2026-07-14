import networkx as nx

def predicate_argument_alignment_score(g_pred: nx.DiGraph, g_gold: nx.DiGraph) -> float:
    """
    PAAS: measures how well predicates and their argument-role structures align.
    g_pred: predicted FOL graph
    g_gold: gold/reference FOL graph
    """
    preds_pred = [n for n, d in g_pred.nodes(data=True) if d.get("type") == "predicate"]
    preds_gold = [n for n, d in g_gold.nodes(data=True) if d.get("type") == "predicate"]

    if not preds_pred and not preds_gold:
        return 1.0

    if not preds_gold:
        return 0.0

    # Index gold predicates by label
    gold_index = {}
    for p in preds_gold:
        label = g_gold.nodes[p].get("label")
        gold_index.setdefault(label, []).append(p)

    matched = 0
    total = max(len(preds_pred), len(preds_gold))

    for p in preds_pred:
        label_p = g_pred.nodes[p].get("label")
        if label_p not in gold_index:
            continue

        # For each candidate gold predicate with same label, compare arg roles
        best = 0
        for pg in gold_index[label_p]:
            args_pred = sorted(
                [d.get("role") for _, _, d in g_pred.out_edges(p, data=True) if d.get("type") == "arg"]
            )
            args_gold = sorted(
                [d.get("role") for _, _, d in g_gold.out_edges(pg, data=True) if d.get("type") == "arg"]
            )
            if args_pred == args_gold:
                best = 1
                break
        matched += best

    return matched / total if total > 0 else 0.0