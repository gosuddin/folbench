# Expected to contain Combiner class
import networkx as nx
from metrics.paas import predicate_argument_alignment_score
from metrics.qss import quantifier_scope_similarity
from metrics.vbc import variable_binding_consistency
from metrics.ted import ted_structural_similarity
from metrics.hung import predicate_alignment_hungarian_similarity
from metrics.cle import equivalence_score

def folbench_score(
g_pred: nx.DiGraph,
g_gold: nx.DiGraph,
w_paas: float = 0.166,
w_qss: float = 0.166,
w_vbc: float = 0.166,
w_cle: float = 0.166,
w_ted: float = 0.166,
w_hungarian: float = 0.166,
) -> float:
    """
    Composite FOLBench score as described in the paper:

    FOLBench = w_paas * PAAS
    + w_qss * QSS
    + w_vbc * VBC
    + w_cle * CLE
    + w_ted * TED
    + w_hungarian * Hungarian

    """
    paas = predicate_argument_alignment_score(g_pred, g_gold)
    qss = quantifier_scope_similarity(g_pred, g_gold)
    vbc = variable_binding_consistency(g_pred, g_gold)
    cle = equivalence_score(g_pred, g_gold)
    ted = ted_structural_similarity(g_pred, g_gold)
    hungarian = predicate_alignment_hungarian_similarity(g_pred, g_gold)

    return (
    w_paas * paas +
    w_qss * qss +
    w_vbc * vbc +
    w_cle * cle +
    w_ted * ted +
    w_hungarian * hungarian
    )