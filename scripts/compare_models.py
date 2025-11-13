#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from collections import defaultdict

def load_results(results_dir):
    results_dir = Path(results_dir)
    model_results = {}

    for model_dir in results_dir.iterdir():
        if not model_dir.is_dir():
            continue

        results_file = model_dir / "batch_results.json"
        if not results_file.exists():
            continue

        try:
            data = json.loads(results_file.read_text())

            if "metadata" in data and "results" in data:
                model_results[model_dir.name] = data
            else:
                model_results[model_dir.name] = {
                    "metadata": {"model": model_dir.name},
                    "results": data
                }
        except Exception as e:
            print(f"Warning: Failed to load {results_file}: {e}", file=sys.stderr)

    return model_results

def print_summary_table(model_results):
    print("\n" + "=" * 100)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 100)
    print()

    headers = ["Model", "Total", "Passed", "Failed", "Pass Rate", "Avg Time", "Total Time"]
    col_widths = [20, 8, 8, 8, 12, 12, 12]

    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * 100)

    for model_name, data in sorted(model_results.items()):
        metadata = data.get("metadata", {})
        results = data.get("results", [])

        total = metadata.get("total_evals", len(results))
        passed = metadata.get("passed", sum(1 for r in results if r.get("passed") is True))
        failed = metadata.get("failed", sum(1 for r in results if r.get("passed") is False))
        pass_rate = metadata.get("pass_rate", round(passed/total*100, 1) if total else 0)
        avg_time = metadata.get("avg_duration_s", 0)
        total_time = metadata.get("total_duration_s", 0)

        row = [
            model_name,
            str(total),
            str(passed),
            str(failed),
            f"{pass_rate:.1f}%",
            f"{avg_time:.1f}s",
            f"{total_time/60:.1f}m"
        ]

        row_str = "  ".join(v.ljust(w) for v, w in zip(row, col_widths))
        print(row_str)

    print()

def analyze_eval_disagreements(model_results):
    eval_outcomes = defaultdict(dict)

    for model_name, data in model_results.items():
        results = data.get("results", [])
        for result in results:
            eval_name = result.get("eval") or result.get("test_id")
            if eval_name:
                eval_outcomes[eval_name][model_name] = result.get("passed")

    disagreements = []
    for eval_name, outcomes in eval_outcomes.items():
        if len(set(outcomes.values())) > 1:
            disagreements.append((eval_name, outcomes))

    if disagreements:
        print("=" * 100)
        print("EVALUATIONS WITH DISAGREEMENTS")
        print("=" * 100)
        print()

        for eval_name, outcomes in sorted(disagreements):
            print(f"  {eval_name}")
            for model_name, passed in sorted(outcomes.items()):
                status = "✓ PASSED" if passed else ("✗ FAILED" if passed is False else "? NULL")
                print(f"    {model_name}: {status}")
            print()
    else:
        print("=" * 100)
        print("No disagreements found - all models agree on all evaluations")
        print("=" * 100)
        print()

def generate_comparison_report(results_dir, model_results):
    output_file = Path(results_dir) / "comparison_summary.json"

    summary = {
        "models": {},
        "disagreements": []
    }

    for model_name, data in model_results.items():
        metadata = data.get("metadata", {})
        results = data.get("results", [])

        total = metadata.get("total_evals", len(results))
        passed = metadata.get("passed", sum(1 for r in results if r.get("passed") is True))

        summary["models"][model_name] = {
            "total_evals": total,
            "passed": passed,
            "failed": metadata.get("failed", total - passed),
            "pass_rate": metadata.get("pass_rate", round(passed/total*100, 1) if total else 0),
            "avg_duration_s": metadata.get("avg_duration_s", 0),
            "total_duration_s": metadata.get("total_duration_s", 0),
        }

    eval_outcomes = defaultdict(dict)
    for model_name, data in model_results.items():
        results = data.get("results", [])
        for result in results:
            eval_name = result.get("eval") or result.get("test_id")
            if eval_name:
                eval_outcomes[eval_name][model_name] = result.get("passed")

    for eval_name, outcomes in eval_outcomes.items():
        if len(set(outcomes.values())) > 1:
            summary["disagreements"].append({
                "eval": eval_name,
                "outcomes": outcomes
            })

    output_file.write_text(json.dumps(summary, indent=2))
    print(f"Comparison report saved to: {output_file}")
    print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_models.py <results_directory>")
        print()
        print("Example:")
        print("  python compare_models.py results/")
        sys.exit(1)

    results_dir = sys.argv[1]

    if not Path(results_dir).exists():
        print(f"Error: Directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    model_results = load_results(results_dir)

    if not model_results:
        print(f"Error: No batch_results.json files found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"\nFound results for {len(model_results)} model(s):")
    for model_name in sorted(model_results.keys()):
        print(f"  - {model_name}")

    print_summary_table(model_results)
    analyze_eval_disagreements(model_results)
    generate_comparison_report(results_dir, model_results)

if __name__ == "__main__":
    main()
