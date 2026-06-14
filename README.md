# FOLBench: A Benchmark for Evaluating FOL-to-Graph Translation

FOLBench is a standardized dataset and evaluation suite for assessing the quality of First-Order Logic (FOL) to Graph (RDF/GraphML) translation systems. It provides a rigorous, multi-faceted framework for measuring how well AI models capture logical meaning in graph structures.

## 🎯 Key Features

*   **Multi-Metric Evaluation**: Uses 5 core metrics to evaluate different aspects of translation quality:
    *   **PAAS**: Predicate-Argument Alignment Score (Semantic matching)
    *   **QSS**: Quantifier Scope Similarity (Structural accuracy)
    *   **VBC**: Variable Binding Consistency (Binding accuracy)
    *   **CLE**: Canonicalized Logical Equivalence (Identity testing)
    
*   **Composite Score**: Combines individual metrics into a single `FOLBench Score` (0–1).
*   **Visualization Tools**: Built-in functions to visualize FOL graphs and debug translations.

## 📚 Metrics Overview

| Metric | Description | Range | Use Case |
| :--- | :--- | :--- | :--- |
| **PAAS** | Measures alignment between predicate arguments | 0–1.0 | Semantic correctness |
| **QSS** | Measures quantifier scope structure | 0–1.0 | Structural accuracy |
| **VBC** | Measures variable binding consistency | 0–1.0 | Binding accuracy |
| **CLE** | Checks logical equivalence of graphs | 0–1.0 | Equivalence testing |
| **FOLBench Score** | Composite metric (0–1) | 0–1 | Comprehensive quality score |

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 🔧 Usage

### Basic Evaluation

```python
from FOLBench.metrics import folbench_score, predicate_argument_alignment_score, quantifier_scope_similarity, variable_binding_consistency, equivalence_score, ted_structural_similarity, predicate_alignment_hungarian_similarity, visualize_fol_graph

graph_pred = ...  # Your predicted graph (NetworkX DiGraph)
graph_gold = ...  # The gold standard graph (NetworkX DiGraph)

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

### Using the Evaluation Script

```bash
# Evaluate a single pair
python FOLBench/metrics/evaluate_single.py --pred pred.graphml --gold gold.graphml

# Evaluate all test cases
python FOLBench/metrics/run_evaluation.py
```

### Evaluation Script Options

```bash
python FOLBench/metrics/run_evaluation.py --help
```

**Arguments:**
*   `--dataset`: Path to the dataset JSON file (default: `FOLBench/dataset/test_set.json`)
*   `--results-dir`: Directory to save results (default: `results/`)
*   `--metrics`: Comma-separated list of metrics to compute
*   `--export-graphs`: Export predicted graphs to files

### Dataset Structure

The dataset consists of JSON files containing:

```json
{
    "examples": [
        {
            "uid": "example_1",
            "fol": "ForAll x (Loves x y)",
            "graphs": {
                "pred": "...",
                "gold": "..."
            },
            "metrics": { ... }
        }
    ]
}
```

## 🛠️ Creating Custom Graphs

You can create graphs programmatically using NetworkX:

```python
import networkx as nx
from FOLBench.metrics.utils import build_graph_from_tokens

# Simple predicate graph
g = nx.DiGraph()
g.add_node("root", type="predicate", label="Loves", is_root=True)
g.add_node("x", type="variable", label="x")
g.add_node("y", type="variable", label="y")
g.add_edge("root", "x", type="arg", role="arg1")
g.add_edge("root", "y", type="arg", role="arg2")

# Or from tokens
tokens = ["Loves", "x", "y"]
graph = build_graph_from_tokens(tokens)
```

## 📈 Expected Output

**Console Output:**
```
========================================
FOLBench Evaluation Results
========================================

Dataset: test_set.json (4 examples)

========================================
Metric Details:
----------------------------------------
PAAS:   0.8500
QSS:    0.9000
VBC:    1.0000
CLE:    0.7500
TED:    0.6000
----------------------------------------
Composite FOLBench Score: 0.81/1.00
========================================
```

**JSON Output (results/metrics_summary.json):**
```json
{
    "dataset": "test_set.json",
    "n_examples": 4,
    "metrics": {
        "paas": 0.85,
        "qss": 0.90,
        "vbc": 1.00,
        "cle": 0.75,
        "ted": 0.60
    },
    "composite_score": 0.81,
    "per_example": [
        {
            "uid": "example_1",
            "fol": "ForAll x (Loves x y)",
            "paas": 1.0,
            "qss": 1.0,
            "vbc": 1.0,
            "cle": 1.0,
            "ted": 0.0,
            "composite_score": 1.0
        }
    ]
}
```

## 🧩 Understanding the Metrics

### PAAS (Predicate-Argument Alignment Score)
Measures the semantic alignment between predicate arguments.
*   **High score**: Predicate labels match and argument positions are correct.
*   **Low score**: Different predicate labels or swapped arguments.

### QSS (Quantifier Scope Similarity)
Measures the structural similarity of quantifier scope using tree edit distance.
*   **High score**: Nested quantifiers correctly preserved.
*   **Low score**: Flattened or reordered quantifiers.

### VBC (Variable Binding Consistency)
Measures how well variables are bound by their quantifiers.
*   **High score**: Every quantifier correctly bound to its variables.
*   **Low score**: Missing or incorrect variable bindings.

### CLE (Canonicalized Logical Equivalence)
Checks if the two graphs are logically equivalent after canonicalization.
*   **1.0**: Graphs are logically equivalent.
*   **0.0**: Graphs are logically different.

## 📊 Composite Score Calculation

The final score is a weighted average of the individual metrics:

```
FOLBench Score = (w1*PAAS + w2*QSS + w3*VBC + w4*CLE + w5*TED)
```

By default, all metrics have equal weight (0.2).

## 🧪 Testing

Run unit tests to verify metric correctness:
