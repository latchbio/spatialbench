import json
import os
import subprocess
import time
from pathlib import Path

EVAL_TIMEOUT = 600


def run_plotsagent_task(
    task_prompt: str,
    work_dir: Path,
    model_name: str | None = None,
    eval_timeout: int = EVAL_TIMEOUT,
) -> dict:
    agent_log_file = work_dir / "agent_output.log"
    if agent_log_file.exists():
        agent_log_file.unlink()

    eval_config = {
        "id": work_dir.name,
        "task": task_prompt,
        "data_node": None,
        "grader": None,
    }

    eval_file = work_dir / "eval_config.json"
    eval_file.write_text(json.dumps(eval_config, indent=2))

    output_file = work_dir / "eval_output.json"

    faas_python = Path(os.environ.get("PLOTS_FAAS_PYTHON", "/root/plots-faas-venv/bin/python"))

    cmd = [
        str(faas_python),
        "-m", "latch_plots_eval_harness.eval_server",
        "--headless",
        "--no-notebook",
        "--eval", str(eval_file),
        "-o", str(output_file),
    ]

    env = {
        **os.environ,
        "LATCH_PLOTS_FAAS_PATH": os.environ.get("LATCH_PLOTS_FAAS_PATH", "/root/latch-plots-faas"),
    }

    start_time = time.time()
    timed_out = False

    try:
        with open(agent_log_file, "w") as log_f:
            subprocess.run(
                cmd,
                env=env,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                timeout=eval_timeout,
            )
    except subprocess.TimeoutExpired:
        timed_out = True
        with open(agent_log_file, "a") as log_f:
            log_f.write(f"\n\nAgent timed out after {eval_timeout} seconds")

    duration = time.time() - start_time
    print(f"Agent output saved to: {agent_log_file}")

    eval_id = work_dir.name
    workspace_dir = output_file.parent / "workspaces" / eval_id

    trajectory = []
    if workspace_dir.exists():
        trajectory_src = workspace_dir / "trajectory.json"
        if trajectory_src.exists():
            try:
                trajectory = json.loads(trajectory_src.read_text())
                trajectory_dst = work_dir / "trajectory.json"
                trajectory_dst.write_text(json.dumps(trajectory, indent=2))
                print(f"Trajectory saved to: {trajectory_dst}")
            except json.JSONDecodeError:
                pass

    agent_answer = None
    error_details = None

    if output_file.exists():
        try:
            results = json.loads(output_file.read_text())
            evals = results.get("evals", [])
            if evals:
                eval_entry = evals[0]
                agent_answer = eval_entry.get("agent_answer")
                if agent_answer is not None:
                    eval_answer_file = work_dir / "eval_answer.json"
                    eval_answer_file.write_text(json.dumps(agent_answer, indent=2))
        except json.JSONDecodeError as e:
            error_details = {"error": f"Failed to parse output: {e}"}

    if agent_answer is None:
        eval_answer_file = work_dir / "eval_answer.json"
        if eval_answer_file.exists():
            try:
                agent_answer = json.loads(eval_answer_file.read_text())
            except json.JSONDecodeError:
                pass

    if agent_answer is None:
        if workspace_dir.exists():
            ws_eval_answer = workspace_dir / "eval_answer.json"
            if ws_eval_answer.exists():
                try:
                    agent_answer = json.loads(ws_eval_answer.read_text())
                    eval_answer_file = work_dir / "eval_answer.json"
                    eval_answer_file.write_text(json.dumps(agent_answer, indent=2))
                except json.JSONDecodeError:
                    pass

    if agent_answer is None and not error_details:
        log_tail = ""
        if agent_log_file.exists():
            log_content = agent_log_file.read_text()
            log_tail = log_content[-1000:]

        error_msg = "Agent timed out" if timed_out else "Agent did not produce an answer"
        error_details = {
            "error": error_msg,
            "timed_out": timed_out,
            "log_tail": log_tail,
        }
        print(f"\nWarning: {error_msg}")

    n_steps = len([t for t in trajectory if t.get("type") == "assistant"])

    metadata = {
        "duration_s": round(duration, 2),
        "model": model_name or "anthropic/claude-sonnet-4",
        "n_steps": n_steps,
        "n_messages": len(trajectory),
    }
    if timed_out:
        metadata["timed_out"] = True
        metadata["eval_timeout_seconds"] = eval_timeout
    if error_details:
        metadata["error_details"] = error_details

    return {"answer": agent_answer, "metadata": metadata}
