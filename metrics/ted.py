import networkx as nx

def _extract_scope_tree(g: nx.DiGraph) -> nx.DiGraph | None:
    """
    Extracts a tree capturing quantifier/connective/predicate scope.
    Assumes a single root with is_root=True.
    """
    roots = [n for n, d in g.nodes(data=True) if d.get("is_root")]
    if not roots:
        return None
    root = roots[0]

    tree = nx.DiGraph()
    tree.add_node(root, **g.nodes[root])

    def dfs(u):
        for v in g.successors(u):
            etype = g[u][v].get("type")
            # scope/logical edges define structure
            if etype in ("scope", "logical"):
                tree.add_node(v, **g.nodes[v])
                tree.add_edge(u, v, type=etype)
                dfs(v)
    dfs(root)
    return tree


def _serialize_tree_preorder(tree: nx.DiGraph) -> list[str]:
    """
    Preorder serialization of a tree as a sequence of node labels.
    """
    if tree is None or len(tree.nodes) == 0:
        return []

    roots = [n for n in tree.nodes if tree.in_degree(n) == 0]
    root = roots[0]

    seq = []

    def rec(u):
        label = f"{tree.nodes[u].get('type')}:{tree.nodes[u].get('label')}"
        seq.append(label)
        for v in tree.successors(u):
            rec(v)

    rec(root)
    return seq


def _sequence_edit_distance(a: list[str], b: list[str]) -> int:
    """
    Levenshtein distance over sequences of labels.
    """
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la

    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j

    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1, # deletion
                dp[i][j - 1] + 1, # insertion
                dp[i - 1][j - 1] + cost, # substitution
            )
    return dp[la][lb]


def ted_structural_similarity(g_pred: nx.DiGraph, g_gold: nx.DiGraph) -> float:
    """
    Tree Edit Distance–based structural similarity in [0,1].
    1.0 = identical scope structure, 0.0 = maximally different.
    """
    t_pred = _extract_scope_tree(g_pred)
    t_gold = _extract_scope_tree(g_gold)

    seq_pred = _serialize_tree_preorder(t_pred)
    seq_gold = _serialize_tree_preorder(t_gold)

    if not seq_pred and not seq_gold:
        return 1.0

    dist = _sequence_edit_distance(seq_pred, seq_gold)
    max_len = max(len(seq_pred), len(seq_gold))
    if max_len == 0:
        return 1.0

    return 1.0 - dist / max_len