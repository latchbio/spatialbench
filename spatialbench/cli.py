import click
import json
from pathlib import Path

from spatialbench import EvalRunner, TestCase
from spatialbench.harness import run_minisweagent_task, batch_download_datasets

@click.group()
@click.version_option(version="0.1.0")
def main():
    pass

@main.command()
@click.argument("eval_path", type=click.Path(exists=True))
@click.option("--keep-workspace", is_flag=True, help="Keep the workspace directory after completion")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--agent", type=click.Choice(["minisweagent"]), default=None, help="Agent to use for evaluation")
@click.option("--model", default=None, help="Model name for mini-swe-agent (defaults to MSWEA_MODEL_NAME env var)")
def run(eval_path, keep_workspace, verbose, agent, model):
    click.echo(f"Running evaluation: {eval_path}")

    runner = EvalRunner(eval_path, keep_workspace=keep_workspace)

    if agent == "minisweagent":
        click.echo(f"Using mini-swe-agent{f' with model: {model}' if model else ''}")

        def agent_fn(task_prompt, work_dir):
            return run_minisweagent_task(task_prompt, work_dir, model_name=model)

        result = runner.run(agent_function=agent_fn)

        if result.get("passed"):
            click.echo("\n✓ Evaluation PASSED")
        else:
            click.echo("\n✗ Evaluation FAILED")
    else:
        click.echo("\nNote: No agent specified.")
        click.echo("To integrate with your agent:")
        click.echo("  1. Use EvalRunner programmatically in Python")
        click.echo("  2. Pass agent_function that writes eval_answer.json")
        click.echo("\nExample:")
        click.echo("  from spatialbench import EvalRunner")
        click.echo("  runner = EvalRunner(eval_path)")
        click.echo("  runner.run(agent_function=my_agent)")
        click.echo("\nOr use mini-swe-agent:")
        click.echo("  spatialbench run evals/qc/seeker_qc_basic.json --agent minisweagent")

        result = runner.run()

@main.command()
@click.argument("eval_dir", type=click.Path(exists=True))
@click.option("--agent", type=click.Choice(["minisweagent"]), default=None, help="Agent to use for evaluation")
@click.option("--model", default=None, help="Model name for agent")
@click.option("--output", "-o", type=click.Path(), help="Output directory for results")
@click.option("--parallel", "-p", type=int, default=1, help="Number of parallel workers")
@click.option("--keep-workspace", is_flag=True, help="Keep workspace after each eval")
def batch(eval_dir, agent, model, output, parallel, keep_workspace):
    click.echo(f"Running batch evaluations from: {eval_dir}")

    if parallel > 1:
        click.echo(f"Parallel execution ({parallel} workers) not yet implemented")
        click.echo("Running sequentially...")

    eval_dir = Path(eval_dir)
    eval_files = list(eval_dir.rglob("*.json"))

    click.echo(f"\nFound {len(eval_files)} evaluation(s)")

    if not eval_files:
        click.echo("No evaluation files found!")
        return

    if not agent:
        click.echo("\nNote: No agent specified. Use --agent minisweagent to run evaluations.")
        return

    click.echo("\n" + "=" * 80)
    click.echo("STEP 1: Collecting datasets from all evaluations")
    click.echo("=" * 80)

    all_uris = set()
    for eval_file in eval_files:
        try:
            eval_data = json.loads(eval_file.read_text())
            test_case = TestCase(**eval_data)
            if test_case.data_node:
                if isinstance(test_case.data_node, list):
                    all_uris.update(test_case.data_node)
                else:
                    all_uris.add(test_case.data_node)
        except Exception as e:
            click.echo(f"Warning: Failed to parse {eval_file}: {e}")

    click.echo(f"Found {len(all_uris)} unique dataset(s) to download")

    if all_uris:
        click.echo("\n" + "=" * 80)
        click.echo("STEP 2: Batch downloading datasets")
        click.echo("=" * 80)
        batch_download_datasets(list(all_uris))

    click.echo("\n" + "=" * 80)
    click.echo("STEP 3: Running evaluations")
    click.echo("=" * 80)

    if agent == "minisweagent":
        def agent_fn(task_prompt, work_dir):
            return run_minisweagent_task(task_prompt, work_dir, model_name=model)
    else:
        agent_fn = None

    results = []
    for i, eval_file in enumerate(eval_files, 1):
        click.echo(f"\n[{i}/{len(eval_files)}] Running: {eval_file.name}")
        click.echo("-" * 80)

        try:
            runner = EvalRunner(eval_file, keep_workspace=keep_workspace)
            result = runner.run(agent_function=agent_fn)
            results.append({
                "eval": eval_file.name,
                "passed": result.get("passed"),
                "test_id": result.get("test_id"),
            })

            status = "✓ PASSED" if result.get("passed") else "✗ FAILED"
            click.echo(f"Result: {status}")

        except Exception as e:
            click.echo(f"✗ ERROR: {e}")
            results.append({
                "eval": eval_file.name,
                "passed": False,
                "error": str(e),
            })

    click.echo("\n" + "=" * 80)
    click.echo("BATCH RESULTS")
    click.echo("=" * 80)

    passed = sum(1 for r in results if r.get("passed") is True)
    failed = sum(1 for r in results if r.get("passed") is False)
    errors = sum(1 for r in results if "error" in r)

    click.echo(f"Total: {len(results)} evaluations")
    click.echo(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    click.echo(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    if errors:
        click.echo(f"Errors: {errors}")

    if output:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        results_file = output_path / "batch_results.json"
        results_file.write_text(json.dumps(results, indent=2))
        click.echo(f"\nResults saved to: {results_file}")

@main.command()
@click.argument("results_dir", type=click.Path(exists=True))
@click.option("--output", "-o", default="leaderboard.json", help="Output file")
def leaderboard(results_dir, output):
    click.echo(f"Generating leaderboard from: {results_dir}")
    click.echo(f"Output: {output}")

    click.echo("\nLeaderboard generation not yet implemented.")
    click.echo("Results will be aggregated from batch evaluation runs.")

@main.command()
@click.argument("eval_path", type=click.Path(exists=True))
def validate(eval_path):
    click.echo(f"Validating evaluation: {eval_path}")

    try:
        eval_path = Path(eval_path)
        eval_data = json.loads(eval_path.read_text())

        required_fields = ["id", "task"]
        missing = [f for f in required_fields if f not in eval_data]

        if missing:
            click.echo(f"❌ Missing required fields: {missing}", err=True)
            return

        if "grader" in eval_data:
            grader_type = eval_data["grader"].get("type")
            from spatialbench.graders import GRADER_REGISTRY

            if grader_type not in GRADER_REGISTRY:
                click.echo(f"❌ Unknown grader type: {grader_type}", err=True)
                click.echo(f"Available graders: {list(GRADER_REGISTRY.keys())}")
                return

        click.echo("✓ Validation passed!")
        click.echo(f"  ID: {eval_data['id']}")
        click.echo(f"  Task: {eval_data['task'][:80]}...")
        if "grader" in eval_data:
            click.echo(f"  Grader: {eval_data['grader'].get('type')}")

    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Validation error: {e}", err=True)

@main.command()
@click.option("--category", "-c", help="Filter by category")
def list(category):
    click.echo("SpatialBench Evaluations")
    click.echo("=" * 50)

    from pathlib import Path
    import os

    package_dir = Path(__file__).parent.parent
    evals_dir = package_dir / "evals"

    if not evals_dir.exists():
        click.echo("No evaluations found")
        return

    categories = ["qc", "preprocessing", "clustering", "cell_typing", "differential_expression", "spatial_analysis"]

    for cat in categories:
        if category and cat != category:
            continue

        cat_dir = evals_dir / cat
        if not cat_dir.exists():
            continue

        eval_files = list(cat_dir.glob("*.json"))
        if not eval_files:
            continue

        click.echo(f"\n{cat.replace('_', ' ').title()} ({len(eval_files)})")
        click.echo("-" * 50)

        for eval_file in sorted(eval_files):
            try:
                eval_data = json.loads(eval_file.read_text())
                click.echo(f"  • {eval_data['id']}")
            except:
                click.echo(f"  • {eval_file.stem}")

if __name__ == "__main__":
    main()
