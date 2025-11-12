#!/usr/bin/env python3

import sys
from pathlib import Path

from spatialbench import EvalRunner, run_minisweagent_task

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_with_minisweagent.py <eval_file> [--keep-workspace]")
        print("\nExample:")
        print("  python run_with_minisweagent.py evals/qc/seeker_qc_basic.json")
        print("  python run_with_minisweagent.py evals/clustering/xenium_leiden.json --keep-workspace")
        sys.exit(1)

    eval_file = sys.argv[1]
    keep_workspace = "--keep-workspace" in sys.argv

    print(f"Running evaluation: {eval_file}")
    print(f"Using mini-swe-agent")
    print()

    runner = EvalRunner(eval_file, keep_workspace=keep_workspace)
    result = runner.run(agent_function=run_minisweagent_task)

    print("\n" + "=" * 80)
    print("EVALUATION RESULT")
    print("=" * 80)

    if result.get("passed"):
        print("✓ PASSED")
    elif result.get("passed") is False:
        print("✗ FAILED")
    else:
        print("⚠ NO GRADER (evaluation ran but was not graded)")

    if result.get("agent_answer"):
        print("\nAgent Answer:")
        import json
        print(json.dumps(result["agent_answer"], indent=2))

    if result.get("grader_result"):
        print("\nGrader Metrics:")
        for key, value in result["grader_result"].metrics.items():
            if not isinstance(value, (list, dict)):
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
