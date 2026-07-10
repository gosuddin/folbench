import networkx as nx
import pytest

from metrics import (
predicate_argument_alignment_score,
quantifier_scope_similarity,
variable_binding_consistency,
equivalence_score,
ted_structural_similarity,
predicate_alignment_hungarian_similarity,
folbench_score,
)
# -----------------------
# Helper graph builders
# -----------------------

def make_predicate_graph(pred_name="P", args=("x", "y")):
    g = nx.DiGraph()

    # root predicate
    g.add_node("p", type="predicate", label=pred_name, is_root=True)

    # variables
    for a in args:
        g.add_node(a, type="variable", label=a)
        g.add_edge("p", a, type="arg", role=f"arg{args.index(a)}")

    return g


def make_quantifier_graph(q="forall", var="x", pred="P"):
    g = nx.DiGraph()

    g.add_node("q", type="quantifier", label=q, is_root=True)
    g.add_node(var, type="variable", label=var)
    g.add_node("p", type="predicate", label=pred)

    g.add_edge("q", var, type="binding")
    g.add_edge("q", "p", type="scope")

    return g


def make_binding_graph(q="forall", vars=("x", "y")):
    g = nx.DiGraph()
    g.add_node("q", type="quantifier", label=q, is_root=True)

    for v in vars:
        g.add_node(v, type="variable", label=v)
        g.add_edge("q", v, type="binding")

    return g


# -----------------------
# Tests for PAAS
# -----------------------

def test_paas_exact_match():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Loves", ("x", "y"))
    assert predicate_argument_alignment_score(g1, g2) == 1.0


def test_paas_mismatched_predicate():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Hates", ("x", "y"))
    assert predicate_argument_alignment_score(g1, g2) == 0.0


def test_paas_mismatched_roles():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Loves", ("y", "x")) # reversed roles
    assert predicate_argument_alignment_score(g1, g2) == 0.0


# -----------------------
# Tests for QSS
# -----------------------

def test_qss_exact_match():
    g1 = make_quantifier_graph("forall", "x", "P")
    g2 = make_quantifier_graph("forall", "x", "P")
    assert quantifier_scope_similarity(g1, g2) == 1.0


def test_qss_quantifier_reversal():
    g1 = make_quantifier_graph("forall", "x", "P")
    g2 = make_quantifier_graph("exists", "x", "P")
    assert quantifier_scope_similarity(g1, g2) < 1.0


def test_qss_empty_graphs():
    g1 = nx.DiGraph()
    g2 = nx.DiGraph()
    assert quantifier_scope_similarity(g1, g2) == 1.0


# -----------------------
# Tests for VBC
# -----------------------

def test_vbc_exact_match():
    g1 = make_binding_graph("forall", ("x", "y"))
    g2 = make_binding_graph("forall", ("x", "y"))
    assert variable_binding_consistency(g1, g2) == 1.0


def test_vbc_mismatch():
    g1 = make_binding_graph("forall", ("x", "y"))
    g2 = make_binding_graph("forall", ("x",))
    assert variable_binding_consistency(g1, g2) < 1.0


def test_vbc_empty():
    g1 = nx.DiGraph()
    g2 = nx.DiGraph()
    assert variable_binding_consistency(g1, g2) == 1.0


# -----------------------
# Tests for Canonical Equivalence
# -----------------------

def test_equivalence_true():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Loves", ("x", "y"))
    assert equivalence_score(g1, g2) == 1.0


def test_equivalence_false():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Hates", ("x", "y"))
    assert equivalence_score(g1, g2) == 0.0

# -----------------------
# Tests for Composite Score
# -----------------------
def test_folbench_score_identical():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Loves", ("x", "y"))
    score = folbench_score(g1, g2, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)
    assert score == pytest.approx(1.0)


def test_folbench_score_different():
    g1 = make_predicate_graph("Loves", ("x", "y"))
    g2 = make_predicate_graph("Hates", ("x", "y"))
    score = folbench_score(g1, g2, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)
    assert score < 1.0
