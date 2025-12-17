import click
import json
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from spatialbench import EvalRunner, TestCase
from spatialbench.harness import run_minisweagent_task, batch_download_datasets

def _run_single_eval(eval_file_path, agent, model, keep_workspace, run_id=None):
    eval_file = Path(eval_file_path)
    start_time = time.time()

    if agent == "minisweagent":
        def agent_fn(task_prompt, work_dir):
            return run_minisweagent_task(task_prompt, work_dir, model_name=model)
    else:
        agent_fn = None

    try:
        runner = EvalRunner(eval_file, keep_workspace=keep_workspace, run_id=run_id)
        result = runner.run(agent_function=agent_fn)
        duration = time.time() - start_time

        output = {
            "eval": eval_file.name,
            "passed": result.get("passed"),
            "test_id": result.get("test_id"),
            "model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_s": round(duration, 2),
        }

        if "metadata" in result:
            output.update(result["metadata"])

        return output
    except Exception as e:
        duration = time.time() - start_time
        return {
            "eval": eval_file.name,
            "passed": False,
            "error": str(e),
            "model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_s": round(duration, 2),
        }

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

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    click.echo(f"Run ID: {run_id}")

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

    if parallel > 1:
        click.echo(f"Running {len(eval_files)} evaluations with {parallel} parallel workers\n")

        results = []
        completed = 0

        with ProcessPoolExecutor(max_workers=parallel) as executor:
            future_to_eval = {
                executor.submit(_run_single_eval, str(eval_file), agent, model, keep_workspace, run_id): eval_file
                for eval_file in eval_files
            }

            for future in as_completed(future_to_eval):
                eval_file = future_to_eval[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    status = "✓ PASSED" if result.get("passed") else "✗ FAILED"
                    click.echo(f"[{completed}/{len(eval_files)}] {eval_file.name}: {status}")

                except Exception as e:
                    click.echo(f"[{completed}/{len(eval_files)}] {eval_file.name}: ✗ ERROR: {e}")
                    results.append({
                        "eval": eval_file.name,
                        "passed": False,
                        "error": str(e),
                    })
    else:
        results = []
        for i, eval_file in enumerate(eval_files, 1):
            click.echo(f"\n[{i}/{len(eval_files)}] Running: {eval_file.name}")
            click.echo("-" * 80)

            start_time = time.time()

            try:
                runner = EvalRunner(eval_file, keep_workspace=keep_workspace, run_id=run_id)

                if agent == "minisweagent":
                    def agent_fn(task_prompt, work_dir):
                        return run_minisweagent_task(task_prompt, work_dir, model_name=model)
                else:
                    agent_fn = None

                result = runner.run(agent_function=agent_fn)
                duration = time.time() - start_time

                eval_output = {
                    "eval": eval_file.name,
                    "passed": result.get("passed"),
                    "test_id": result.get("test_id"),
                    "model": model,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "duration_s": round(duration, 2),
                }

                if "metadata" in result:
                    eval_output.update(result["metadata"])

                results.append(eval_output)

                status = "✓ PASSED" if result.get("passed") else "✗ FAILED"
                click.echo(f"Result: {status}")

            except Exception as e:
                duration = time.time() - start_time
                click.echo(f"✗ ERROR: {e}")
                results.append({
                    "eval": eval_file.name,
                    "passed": False,
                    "error": str(e),
                    "model": model,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "duration_s": round(duration, 2),
                })

    click.echo("\n" + "=" * 80)
    click.echo("BATCH RESULTS")
    click.echo("=" * 80)

    passed = sum(1 for r in results if r.get("passed") is True)
    failed = sum(1 for r in results if r.get("passed") is False)
    errors = sum(1 for r in results if "error" in r)

    durations = [r.get("duration_s", 0) for r in results if "duration_s" in r]
    avg_duration = sum(durations) / len(durations) if durations else 0
    total_duration = sum(durations)

    costs = [r.get("total_cost", 0) for r in results if r.get("total_cost") is not None]
    total_cost = sum(costs) if costs else None
    avg_cost = sum(costs) / len(costs) if costs else None

    steps = [r.get("n_steps", 0) for r in results if r.get("n_steps") is not None]
    total_steps = sum(steps) if steps else None
    avg_steps = sum(steps) / len(steps) if steps else None

    click.echo(f"Total: {len(results)} evaluations")
    click.echo(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    click.echo(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    if errors:
        click.echo(f"Errors: {errors}")
    click.echo(f"Average duration: {avg_duration:.1f}s")
    click.echo(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f}m)")
    if total_cost is not None:
        click.echo(f"Total cost: ${total_cost:.4f}")
        click.echo(f"Average cost per eval: ${avg_cost:.4f}")
    if total_steps is not None:
        click.echo(f"Total steps: {total_steps}")
        click.echo(f"Average steps per eval: {avg_steps:.1f}")
    if model:
        click.echo(f"Model: {model}")

    if output:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            "model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eval_dir": str(eval_dir),
            "total_evals": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": round(passed/len(results)*100, 1) if results else 0,
            "avg_duration_s": round(avg_duration, 2),
            "total_duration_s": round(total_duration, 2),
        }

        if total_cost is not None:
            metadata["total_cost"] = round(total_cost, 4)
            metadata["avg_cost_per_eval"] = round(avg_cost, 4)

        if total_steps is not None:
            metadata["total_steps"] = total_steps
            metadata["avg_steps_per_eval"] = round(avg_steps, 1)

        batch_summary = {
            "metadata": metadata,
            "results": results
        }

        results_file = output_path / "batch_results.json"
        results_file.write_text(json.dumps(batch_summary, indent=2))
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

@main.command(name="list")
@click.option("--category", "-c", help="Filter by category")
def list_evals(category):
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
