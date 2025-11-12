import click
import json
from pathlib import Path

from spatialbench import EvalRunner

@click.group()
@click.version_option(version="0.1.0")
def main():
    pass

@main.command()
@click.argument("eval_path", type=click.Path(exists=True))
@click.option("--keep-workspace", is_flag=True, help="Keep the workspace directory after completion")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(eval_path, keep_workspace, verbose):
    click.echo(f"Running evaluation: {eval_path}")

    runner = EvalRunner(eval_path, keep_workspace=keep_workspace)

    click.echo("\nNote: No agent function provided.")
    click.echo("To integrate with your agent:")
    click.echo("  1. Use EvalRunner programmatically in Python")
    click.echo("  2. Pass agent_function that writes eval_answer.json")
    click.echo("\nExample:")
    click.echo("  from spatialbench import EvalRunner")
    click.echo("  runner = EvalRunner(eval_path)")
    click.echo("  runner.run(agent_function=my_agent)")

    result = runner.run()

@main.command()
@click.argument("eval_dir", type=click.Path(exists=True))
@click.option("--model", default="default", help="Model name for results tracking")
@click.option("--output", "-o", type=click.Path(), help="Output directory for results")
@click.option("--parallel", "-p", type=int, default=1, help="Number of parallel workers")
def batch(eval_dir, model, output, parallel):
    click.echo(f"Running batch evaluations from: {eval_dir}")
    click.echo(f"Model: {model}")

    if parallel > 1:
        click.echo(f"Parallel execution ({parallel} workers) not yet implemented")
        click.echo("Running sequentially...")

    eval_dir = Path(eval_dir)
    eval_files = list(eval_dir.rglob("*.json"))

    click.echo(f"\nFound {len(eval_files)} evaluation(s)")

    if not eval_files:
        click.echo("No evaluation files found!")
        return

    click.echo("\nNote: Batch execution requires agent integration.")
    click.echo("This CLI provides the framework - integrate your agent to run evaluations.")

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
