# FOLBench: A Benchmark for Evaluating Natural Language from a Logical Coherence and Correctness POV

FOLBench is an evaluation suite for assessing the quality of Logical Coherence and Correctness by feeding First-Order Logic (FOL) of the corresponding Natural Language. It provides a deterministic, reproducible, and multi-faceted framework for measuring how well logically aligned are they in graph structures.

## 🎯 Key Features

*   **Multi-Metric Evaluation**: Uses 6 core metrics to evaluate different aspects of logical coherence and correctness quality:
    *   **PAAS**: Predicate-Argument Alignment Score (Semantic matching)
    *   **QSS**: Quantifier Scope Similarity (Structural accuracy)
    *   **VBC**: Variable Binding Consistency (Binding accuracy)
    *   **CLE**: Canonicalized Logical Equivalence (Identity testing)
    *   **TED**: Tree Edit Distance (Structural Edits)
    *   **HS**: Hungarian Similarity (Structural Matching)
    
*   **Composite Score**: Combines individual metrics into a single `FOLBench Score` (0–1).
*   **Visualization Tools**: Built-in functions to visualize FOL graphs and debug translations.

## 📚 Metrics Overview

| Metric | Description | Range | Use Case |
| :--- | :--- | :--- | :--- |
| **PAAS** | Measures alignment between predicate arguments | 0–1.0 | Semantic correctness |
| **QSS** | Measures quantifier scope structure | 0–1.0 | Structural accuracy |
| **VBC** | Measures variable binding consistency | 0–1.0 | Binding accuracy |
| **CLE** | Checks logical equivalence of graphs | 0–1.0 | Equivalence testing |
| **TED** | Checks structural edits needed for logical equivalence of graphs | 0–1.0 | Equivalence testing |
| **HS** | Checks matching cost for logical equivalence of graphs | 0–1.0 | Equivalence testing |
| **FOLBench Score** | Composite metric (0–1) | 0–1 | Comprehensive logical coherence and correctness score |

## 🚀 Installation

```bash
pip install folbench
```

## 🔧 Usage

### Basic Evaluation

```python
from FOLBench.metrics import folbench_score, predicate_argument_alignment_score, quantifier_scope_similarity, variable_binding_consistency, equivalence_score, ted_structural_similarity, predicate_alignment_hungarian_similarity, visualize_fol_graph

graph_pred = ...  # Your predicted First-Order Logic formula
graph_gold = ...  # The gold standard First-Order Logic formula

# Calculate composite score
score = folbench_score(graph_pred, graph_gold)
print(f"FOLBench Score: {score:.2f}")

# Individual metrics
paas = predicate_argument_alignment_score(graph_pred, graph_gold)
qss = quantifier_scope_similarity(graph_pred, graph_gold)
vbc = variable_binding_consistency(graph_pred, graph_gold)
cle = equivalence_score(graph_pred, graph_gold)
ted_score = ted(graph_pred, graph_gold)

# Visualize graphs
visualize_fol_graph(graph_pred, title="Predicted Graph")
visualize_fol_graph(graph_gold, title="Gold Graph")

```

## 📊 Composite Score Calculation

The final score is a weighted average of the individual metrics:

```
FOLBench Score = (w1*PAAS + w2*QSS + w3*VBC + w4*CLE + w5*TED + w6*HS)
```

By default, all metrics have equal weight (0.16) but are customizable.

