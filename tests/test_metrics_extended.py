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


# ---------------------------------------------------------
# Helper graph builders
# ---------------------------------------------------------

def pred_graph(label, args):
    g = nx.DiGraph()
    g.add_node("root", type="predicate", label=label, is_root=True)
    for i, a in enumerate(args):
        g.add_node(a, type="variable", label=a)
        g.add_edge("root", a, type="arg", role=f"arg{i}")
    return g


def quant_graph(qtype, var, pred):
    g = nx.DiGraph()
    g.add_node("q", type="quantifier", label=qtype, is_root=True)
    g.add_node(var, type="variable", label=var)
    g.add_node("p", type="predicate", label=pred)
    g.add_edge("q", var, type="binding")
    g.add_edge("q", "p", type="scope")
    return g


def nested_quant_graph():
    # ∀x ∃y P(x,y)
    g = nx.DiGraph()
    g.add_node("forall", type="quantifier", label="forall", is_root=True)
    g.add_node("exists", type="quantifier", label="exists")
    g.add_node("x", type="variable", label="x")
    g.add_node("y", type="variable", label="y")
    g.add_node("p", type="predicate", label="P")

    g.add_edge("forall", "x", type="binding")
    g.add_edge("forall", "exists", type="scope")
    g.add_edge("exists", "y", type="binding")
    g.add_edge("exists", "p", type="scope")
    g.add_edge("p", "x", type="arg", role="arg0")
    g.add_edge("p", "y", type="arg", role="arg1")
    return g


def reversed_nested_quant_graph():
    # ∃y ∀x P(x,y)
    g = nx.DiGraph()
    g.add_node("exists", type="quantifier", label="exists", is_root=True)
    g.add_node("forall", type="quantifier", label="forall")
    g.add_node("x", type="variable", label="x")
    g.add_node("y", type="variable", label="y")
    g.add_node("p", type="predicate", label="P")

    g.add_edge("exists", "y", type="binding")
    g.add_edge("exists", "forall", type="scope")
    g.add_edge("forall", "x", type="binding")
    g.add_edge("forall", "p", type="scope")
    g.add_edge("p", "x", type="arg", role="arg0")
    g.add_edge("p", "y", type="arg", role="arg1")
    return g


# ---------------------------------------------------------
# PAAS Extended Tests
# ---------------------------------------------------------

def test_paas_predicate_hallucination():
    g1 = pred_graph("Loves", ("x", "y"))
    g2 = pred_graph("Loves", ("x", "y"))
    g1.add_node("fake", type="predicate", label="Hallucinated")
    assert predicate_argument_alignment_score(g1, g2) < 1.0


def test_paas_missing_argument():
    g1 = pred_graph("Loves", ("x",))
    g2 = pred_graph("Loves", ("x", "y"))
    assert predicate_argument_alignment_score(g1, g2) < 1.0


def test_paas_extra_argument():
    g1 = pred_graph("Loves", ("x", "y", "z"))
    g2 = pred_graph("Loves", ("x", "y"))
    assert predicate_argument_alignment_score(g1, g2) < 1.0


# ---------------------------------------------------------
# QSS Extended Tests
# ---------------------------------------------------------

def test_qss_nested_quantifiers():
    g1 = nested_quant_graph()
    g2 = nested_quant_graph()
    assert quantifier_scope_similarity(g1, g2) == 1.0


def test_qss_nested_scope_reversal():
    g1 = nested_quant_graph()
    g2 = reversed_nested_quant_graph()
    assert quantifier_scope_similarity(g1, g2) < 0.5


def test_qss_predicate_under_wrong_scope():
    g1 = nested_quant_graph()
    g2 = nested_quant_graph()
    # Move predicate under wrong quantifier
    g2.remove_edge("exists", "p")
    g2.add_edge("forall", "p", type="scope")
    assert quantifier_scope_similarity(g1, g2) < 1.0


# ---------------------------------------------------------
# VBC Extended Tests
# ---------------------------------------------------------

def test_vbc_variable_reuse_error():
    g1 = quant_graph("forall", "x", "P")
    g2 = quant_graph("forall", "x", "P")
    # Reuse variable incorrectly
    g2.add_node("x2", type="variable", label="x")
    g2.add_edge("q", "x2", type="binding")
    assert variable_binding_consistency(g1, g2) < 1.0


def test_vbc_wrong_quantifier_binding():
    g1 = quant_graph("forall", "x", "P")
    g2 = quant_graph("exists", "x", "P")
    assert variable_binding_consistency(g1, g2) < 1.0


# ---------------------------------------------------------
# Canonical Equivalence Extended Tests
# ---------------------------------------------------------

def test_equivalence_variable_renaming():
    g1 = pred_graph("Loves", ("x", "y"))
    g2 = pred_graph("Loves", ("a", "b"))
    # Canonicalization should make them equivalent
    assert equivalence_score(g1, g2) == 1.0


def test_equivalence_argument_swap_not_equivalent():
    g1 = pred_graph("Loves", ("x", "y"))
    g2 = pred_graph("Loves", ("y", "x"))
    assert equivalence_score(g1, g2) == 0.0


# ---------------------------------------------------------
# Composite Score Extended Tests
# ---------------------------------------------------------


def test_composite_score_monotonicity():
    g1 = pred_graph("Loves", ("x", "y"))
    g2 = pred_graph("Loves", ("x", "y"))
    g3 = pred_graph("Hates", ("x", "y"))

    score_same = folbench_score(g1, g2, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)
    score_diff = folbench_score(g1, g3, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)

    assert score_same > score_diff


def test_composite_score_penalizes_scope_errors():
    g1 = nested_quant_graph()
    g2 = reversed_nested_quant_graph()
    score = folbench_score(g1, g2, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)
    assert score < 0.7


def test_composite_score_penalizes_binding_errors():
    g1 = quant_graph("forall", "x", "P")
    g2 = quant_graph("forall", "x", "P")
    g2.add_node("x2", type="variable", label="x")
    g2.add_edge("q", "x2", type="binding")
    score = folbench_score(g1, g2, 1/6, 1/6, 1/6, 1/6, 1/6, 1/6)
    assert score < 1.0