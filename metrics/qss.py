import networkx as nx

def _extract_scope_tree(g: nx.DiGraph) -> nx.DiGraph | None:
    """
    Extracts a quantifier/connective scope tree rooted at the top-level node.
    Assumes a single root node marked with is_root=True.
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
            if etype in ("scope", "logical"):
                tree.add_node(v, **g.nodes[v])
                tree.add_edge(u, v, type=etype)
                dfs(v)

    dfs(root)
    return tree

def _serialize_tree(tree: nx.DiGraph) -> str:
    """
    Serializes a scope tree into a string for simple edit-distance-based similarity.
    """
    if tree is None or len(tree.nodes) == 0:
        return ""

    roots = [n for n in tree.nodes if tree.in_degree(n) == 0]
    root = roots[0]

    def rec(u):
        children = list(tree.successors(u))
        children_str = ",".join(rec(c) for c in children)
        return f"({tree.nodes[u].get('type')}:{tree.nodes[u].get('label')}[{children_str}])"

    return rec(root)


def _levenshtein(a: str, b: str) -> int:
    """
    Simple Levenshtein distance for strings.
    """
    if a == b:
        return 0
    la, lb = len(a), len(b)
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
)
    return dp[la][lb]


def quantifier_scope_similarity(g_pred: nx.DiGraph, g_gold: nx.DiGraph) -> float:
    """
    QSS: compares quantifier/connective scope structure via normalized edit distance
    over serialized scope trees.
    """
    t_pred = _extract_scope_tree(g_pred)
    t_gold = _extract_scope_tree(g_gold)

    if t_pred is None and t_gold is None:
        return 1.0

    s_pred = _serialize_tree(t_pred)
    s_gold = _serialize_tree(t_gold)

    if not s_pred and not s_gold:
        return 1.0
    if not s_pred or not s_gold:
        return 0.0

    dist = _levenshtein(s_pred, s_gold)
    max_len = max(len(s_pred), len(s_gold))
    return 1.0 - dist / max_len