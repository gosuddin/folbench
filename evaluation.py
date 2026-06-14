#!/usr/bin/env python3
import argparse
import csv
import networkx as nx

from folbench import (
 predicate_argument_alignment_score,
 quantifier_scope_similarity,
 variable_binding_consistency,
 equivalence_score,
 ted_structural_similarity,
 predicate_alignment_hungarian_similarity,
 folbench_score,
)


# ---------------------------------------------------------
# Placeholder parser — replace with your NL→FOL → graph code
# ---------------------------------------------------------
def parse_fol_to_graph(fol_str: str) -> nx.DiGraph:
    """
    Convert a FOL string into a FOLBench graph.
    Replace this with your actual parser.
    """
    g = nx.DiGraph()
    # Minimal placeholder: one predicate node
    g.add_node("root", type="predicate", label=fol_str, is_root=True)
    return g


# ---------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------
def evaluate_tsv(tsv_path: str):
    results = []

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            ex_id = row["id"]
            pred_fol = row["pred_fol"]
            gold_fol = row["gold_fol"]

            # Convert to graphs
            g_pred = parse_fol_to_graph(pred_fol)
            g_gold = parse_fol_to_graph(gold_fol)

            # Compute metrics
            paas = predicate_argument_alignment_score(g_pred, g_gold)
            qss = quantifier_scope_similarity(g_pred, g_gold)
            vbc = variable_binding_consistency(g_pred, g_gold)
            eq = equivalence_score(g_pred, g_gold)
            ted = ted_structural_similarity(g_pred, g_gold)
            hung = predicate_alignment_hungarian_similarity(g_pred, g_gold)
            composite = folbench_score(g_pred, g_gold)

            results.append({
                "id": ex_id,
                "PAAS": paas,
                "QSS": qss,
                "VBC": vbc,
                "Equivalence": eq,
                "TED": ted,
                "Hung": hung,
                "FOLBench": composite,
            })

    return results


# ---------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------
def print_results(results):
    print("\n=== FOLBench Evaluation Results ===\n")
    for r in results:
        print(f"ID: {r['id']}")
        print(f" PAAS: {r['PAAS']:.4f}")
        print(f" QSS: {r['QSS']:.4f}")
        print(f" VBC: {r['VBC']:.4f}")
        print(f" Equivalence: {r['Equivalence']:.4f}")
        print(f" TED: {r['TED']:.4f}")
        print(f" Hung: {r['Hung']:.4f}")
        print(f" FOLBench: {r['FOLBench']:.4f}")
        print("-" * 40)


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Evaluate predicted FOL against gold FOL using FOLBench metrics."
    )
    parser.add_argument(
        "--tsv",
        type=str,
        required=True,
        help="Path to TSV file with columns: id, pred_fol, gold_fol",
    )
    args = parser.parse_args()

    results = evaluate_tsv(args.tsv)
    print_results(results)


if __name__ == "__main__":
    main()