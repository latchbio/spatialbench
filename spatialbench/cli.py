import click
import json
import time
from datetime import datetime
from pathlib import Path

from spatialbench import EvalRunner
from latch_eval_tools.harness import (
    run_minisweagent_task,
    run_claudecode_task,
    run_openaicodex_task,
)


agent_registry = {
    "minisweagent": ("mini-swe-agent", run_minisweagent_task),
    "claudecode": ("Claude Code", run_claudecode_task),
    "openaicodex": ("OpenAI Codex", run_openaicodex_task),
}


@click.group()
@click.version_option(version="0.2.0")
def main():
    pass


@main.command()
@click.argument("eval_path", type=click.Path(exists=True))
@click.option(
    "--keep-workspace",
    is_flag=True,
    default=True,
    help="Keep the workspace directory after completion",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--agent",
    type=click.Choice(list(agent_registry.keys())),
    default=None,
    help="Agent to use for evaluation",
)
@click.option("--model", default=None, help="Model name for agent")
def run(eval_path, keep_workspace, verbose, agent, model):
    click.echo(f"Running evaluation: {eval_path}")

    runner = EvalRunner(eval_path, keep_workspace=keep_workspace)

    if agent not in agent_registry:
        click.echo(
            f"\nNote: No agent specified: available agents are {list(agent_registry.keys())}"
        )
        click.echo("To integrate with your agent:")
        click.echo("  1. Use EvalRunner programmatically in Python")
        click.echo("  2. Pass agent_function that writes eval_answer.json")
        click.echo("\nExample:")
        click.echo("  from spatialbench import EvalRunner")
        click.echo("  runner = EvalRunner(eval_path)")
        click.echo("  runner.run(agent_function=my_agent)")
        click.echo("\nOr use mini-swe-agent:")
        click.echo(
            "  spatialbench run evals/qc/seeker_qc_basic.json --agent minisweagent"
        )
        result = runner.run()
        return

    agent_name, agent_task = agent_registry[agent]
    click.echo(f"Using {agent_name}{f' with model: {model}' if model else ''}")

    def agent_fn(task_prompt, work_dir):
        return agent_task(task_prompt, work_dir, model_name=model)

    result = runner.run(agent_function=agent_fn)

    if result.get("passed"):
        click.echo("\n✓ Evaluation PASSED")
    else:
        click.echo("\n✗ Evaluation FAILED")


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
            from latch_eval_tools.graders import GRADER_REGISTRY

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


if __name__ == "__main__":
    main()
