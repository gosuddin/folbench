import networkx as nx


def _predicate_nodes(g: nx.DiGraph):
    return [n for n, d in g.nodes(data=True) if d.get("type") == "predicate"]


def _predicate_cost(g1, p1, g2, p2) -> float:
    """
    Cost between two predicate nodes based on label and arg roles.
    0 = identical, higher = more different.
    """
    l1 = g1.nodes[p1].get("label")
    l2 = g2.nodes[p2].get("label")

    cost = 0.0
    if l1 != l2:
        cost += 1.0

    args1 = sorted(
        [d.get("role") for _, _, d in g1.out_edges(p1, data=True) if d.get("type") == "arg"]
    )
    args2 = sorted(
        [d.get("role") for _, _, d in g2.out_edges(p2, data=True) if d.get("type") == "arg"]
    )

    # penalize arg role mismatch
    max_len = max(len(args1), len(args2))
    for i in range(max_len):
        r1 = args1[i] if i < len(args1) else None
        r2 = args2[i] if i < len(args2) else None
        if r1 != r2:
            cost += 0.5

    return cost


def hungarian_min_cost(cost_matrix: list[list[float]]) -> float:
    """
    Very simple Hungarian algorithm implementation for square matrices.
    Assumes cost_matrix is n x n.
    Returns minimal total cost.
    """
    import math

    n = len(cost_matrix)
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [math.inf] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = math.inf
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    # p[j] = row assigned to column j
    assignment_cost = -v[0]
    return assignment_cost


def predicate_alignment_hungarian_similarity(g_pred: nx.DiGraph, g_gold: nx.DiGraph) -> float:
    """
    Hungarian alignment–based predicate similarity in [0,1].
    1.0 = perfect alignment, 0.0 = maximally different.
    """
    preds1 = _predicate_nodes(g_pred)
    preds2 = _predicate_nodes(g_gold)

    if not preds1 and not preds2:
        return 1.0

    n = max(len(preds1), len(preds2))
    # pad with dummy predicates
    preds1 = preds1 + [None] * (n - len(preds1))
    preds2 = preds2 + [None] * (n - len(preds2))

    # build cost matrix
    cost_matrix = []
    max_cost = 0.0
    for p1 in preds1:
        row = []
        for p2 in preds2:
            if p1 is None or p2 is None:
                c = 2.0 # cost for missing predicate
            else:
                c = _predicate_cost(g_pred, p1, g_gold, p2)
            row.append(c)
            max_cost = max(max_cost, c)
        cost_matrix.append(row)

    if n == 0:
        return 1.0

    total_cost = hungarian_min_cost(cost_matrix)
    # normalize: worst case = n * max_cost
    worst = n * max_cost if max_cost > 0 else 1.0
    norm = min(total_cost / worst, 1.0)
    return 1.0 - norm