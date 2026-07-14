import networkx as nx

def canonicalize_graph(G):
    """
    Canonicalize a FOLBench graph.
    Works directly on the NetworkX DiGraph produced by your build_graph().
    """

    G = G.copy()

    # ---------------------------------------------------------
    # 1. Normalize variable names
    # ---------------------------------------------------------
    var_nodes = [n for n, d in G.nodes(data=True) if d["type"] == "VAR"]
    var_map = {}
    counter = 1

    for v in sorted(var_nodes):
        var_map[v] = f"x{counter}"
        counter += 1

    for v in var_nodes:
        G.nodes[v]["label"] = var_map[v]

    # ---------------------------------------------------------
    # 2. Normalize commutative operators (AND, OR)
    # ---------------------------------------------------------
    for n, d in G.nodes(data=True):
        if d["type"] in ("AND", "OR"):
            children = list(G.successors(n))
            # sort children by label for canonical ordering
            children_sorted = sorted(children, key=lambda c: G.nodes[c]["label"])
            # remove old edges
            for c in children:
                G.remove_edge(n, c)
            # add sorted edges
            for c in children_sorted:
                G.add_edge(n, c)

    # ---------------------------------------------------------
    # 3. Flatten nested AND/OR nodes
    # ---------------------------------------------------------
    for n, d in list(G.nodes(data=True)):
        if d["type"] in ("AND", "OR"):
            children = list(G.successors(n))
            flat = []
            for c in children:
                if G.nodes[c]["type"] == d["type"]:
                    flat.extend(list(G.successors(c)))
                else:
                    flat.append(c)

            # rewrite edges
            for c in children:
                G.remove_edge(n, c)
            for c in flat:
                G.add_edge(n, c)

    # ---------------------------------------------------------
    # 4. Normalize negation (double negation + De Morgan)
    # ---------------------------------------------------------
    for n, d in list(G.nodes(data=True)):
        if d["type"] == "NOT":
            child = next(G.successors(n), None)
            if child is None:
                continue

            # double negation
            if G.nodes[child]["type"] == "NOT":
                grandchild = next(G.successors(child))
                # redirect edges
                G.remove_edge(n, child)
                G.add_edge(n, grandchild)

            # De Morgan
            if G.nodes[child]["type"] == "AND":
                # ¬(A ∧ B) → (¬A ∨ ¬B)
                new_or = f"{n}_OR"
                G.add_node(new_or, type="OR", label="OR")
                for c in G.successors(child):
                    neg = f"{c}_NEG"
                    G.add_node(neg, type="NOT", label="NOT")
                    G.add_edge(neg, c)
                    G.add_edge(new_or, neg)
                # redirect parent edges
                for p in list(G.predecessors(n)):
                    G.remove_edge(p, n)
                    G.add_edge(p, new_or)

            if G.nodes[child]["type"] == "OR":
                # ¬(A ∨ B) → (¬A ∧ ¬B)
                new_and = f"{n}_AND"
                G.add_node(new_and, type="AND", label="AND")
                for c in G.successors(child):
                    neg = f"{c}_NEG"
                    G.add_node(neg, type="NOT", label="NOT")
                    G.add_edge(neg, c)
                    G.add_edge(new_and, neg)
                for p in list(G.predecessors(n)):
                    G.remove_edge(p, n)
                    G.add_edge(p, new_and)

    # ---------------------------------------------------------
    # 5. Normalize implication and equivalence
    # ---------------------------------------------------------
    for n, d in list(G.nodes(data=True)):
        if d["type"] == "IMPLIES":
            A, B = list(G.successors(n))
            # A → B = ¬A ∨ B
            new_or = f"{n}_OR"
            G.add_node(new_or, type="OR", label="OR")

            negA = f"{A}_NEG"
            G.add_node(negA, type="NOT", label="NOT")
            G.add_edge(negA, A)

            G.add_edge(new_or, negA)
            G.add_edge(new_or, B)

            for p in list(G.predecessors(n)):
                G.remove_edge(p, n)
                G.add_edge(p, new_or)

        if d["type"] == "IFF":
            A, B = list(G.successors(n))
            # A ↔ B = (A → B) ∧ (B → A)
            new_and = f"{n}_AND"
            G.add_node(new_and, type="AND", label="AND")

            # A → B
            impl1 = f"{n}_IMPL1"
            G.add_node(impl1, type="IMPLIES", label="IMPLIES")
            G.add_edge(impl1, A)
            G.add_edge(impl1, B)

            # B → A
            impl2 = f"{n}_IMPL2"
            G.add_node(impl2, type="IMPLIES", label="IMPLIES")
            G.add_edge(impl2, B)
            G.add_edge(impl2, A)

            G.add_edge(new_and, impl1)
            G.add_edge(new_and, impl2)

            for p in list(G.predecessors(n)):
                G.remove_edge(p, n)
                G.add_edge(p, new_and)

    return G

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
    g1 = canonicalize_graph(g1)
    g2 = canonicalize_graph(g2)
    return 1.0 if canonicalized_logical_equivalence(g1, g2) else 0.0