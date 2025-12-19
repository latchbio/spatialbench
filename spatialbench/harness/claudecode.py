import json
import os
import subprocess
import time
from pathlib import Path

EVAL_TIMEOUT = 600

MODEL_MAP = {
    "anthropic/claude-opus-4-5": "opus",
    "anthropic/claude-sonnet-4-5": "sonnet",
    "anthropic/claude-sonnet-4": "claude-sonnet-4-20250514",
    "anthropic/claude-opus-4": "claude-opus-4-20250514",
    "anthropic/claude-haiku-3-5": "haiku",
}


def run_claudecode_task(
    task_prompt: str,
    work_dir: Path,
    model_name: str | None = None,
    eval_timeout: int = EVAL_TIMEOUT,
) -> dict:
    agent_log_file = work_dir / "agent_output.log"
    if agent_log_file.exists():
        agent_log_file.unlink()

    enhanced_prompt = _enhance_prompt_with_local_files(task_prompt, work_dir)
    enhanced_prompt += """

CRITICAL: You must write eval_answer.json BEFORE signaling completion.
Correct order: 1) Perform analysis 2) Write eval_answer.json with your answer 3) Exit"""

    cmd = ["claude", "--print", "--dangerously-skip-permissions", "--verbose", "--output-format", "stream-json"]

    if model_name:
        claude_model = MODEL_MAP.get(model_name, model_name)
        cmd.extend(["--model", claude_model])

    run_as_claude_user = os.geteuid() == 0
    if run_as_claude_user:
        import pwd
        import shutil
        try:
            pwd.getpwnam("claude")
            spatialbench_dir = Path.home() / ".spatialbench"
            if spatialbench_dir.exists():
                shutil.chown(spatialbench_dir, user="claude", group="claude")
                for item in spatialbench_dir.rglob("*"):
                    try:
                        shutil.chown(item, user="claude", group="claude")
                    except PermissionError:
                        pass
        except KeyError:
            run_as_claude_user = False

    env = os.environ.copy()

    start_time = time.time()
    timed_out = False
    claude_result = None
    trajectory = []

    try:
        if run_as_claude_user:
            env_vars = [f"{k}={v}" for k, v in env.items() if k.endswith("_API_KEY")]
            cmd = ["runuser", "-u", "claude", "--", "env"] + env_vars + cmd

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(work_dir),
            env=env,
            text=True,
        )

        try:
            stdout, stderr = process.communicate(
                input=enhanced_prompt,
                timeout=eval_timeout
            )

            with open(agent_log_file, 'w') as log_file:
                log_file.write(stdout)
                if stderr:
                    log_file.write(f"\n\nSTDERR:\n{stderr}")

            for line in stdout.strip().split('\n'):
                if line:
                    try:
                        event = json.loads(line)
                        trajectory.append(event)
                        if event.get("type") == "result":
                            claude_result = event
                    except json.JSONDecodeError:
                        pass

        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout, stderr = process.communicate()
            with open(agent_log_file, 'w') as log_file:
                log_file.write(stdout)
                log_file.write(f"\n\nAgent timed out after {eval_timeout} seconds")

    except Exception as e:
        with open(agent_log_file, 'a') as f:
            f.write(f"\nError running claude: {e}")

    duration = time.time() - start_time
    print(f"Agent output saved to: {agent_log_file}")

    if trajectory:
        trajectory_file = work_dir / "trajectory.json"
        trajectory_file.write_text(json.dumps(trajectory, indent=2))
        print(f"Trajectory saved to: {trajectory_file}")

    eval_answer_file = work_dir / "eval_answer.json"
    agent_answer = None
    error_details = None

    if not eval_answer_file.exists():
        log_tail = ""
        if agent_log_file.exists():
            log_content = agent_log_file.read_text()
            log_tail = log_content[-1000:]

        error_msg = "Agent timed out" if timed_out else "Agent did not create eval_answer.json"
        error_details = {
            "error": error_msg,
            "timed_out": timed_out,
            "log_tail": log_tail
        }
        print(f"\nWarning: {error_msg}")
    else:
        try:
            agent_answer = json.loads(eval_answer_file.read_text())
        except json.JSONDecodeError as e:
            error_details = {
                "error": f"Failed to parse eval_answer.json: {e}",
                "file_contents": eval_answer_file.read_text()[:500]
            }
            print(f"\nWarning: Failed to parse eval_answer.json: {e}")

    metadata = {
        "duration_s": round(duration, 2),
        "model": model_name,
    }
    if claude_result:
        metadata["total_cost"] = claude_result.get("total_cost_usd")
        metadata["n_turns"] = claude_result.get("num_turns")
        metadata["session_id"] = claude_result.get("session_id")
        metadata["usage"] = claude_result.get("usage")
    if timed_out:
        metadata["timed_out"] = True
        metadata["eval_timeout_seconds"] = eval_timeout
    if error_details:
        metadata["error_details"] = error_details

    return {"answer": agent_answer, "metadata": metadata}


def _enhance_prompt_with_local_files(task_prompt: str, work_dir: Path) -> str:
    import re
    contextual_data_match = re.search(
        r'<ContextualNodeData>(.*?)</ContextualNodeData>',
        task_prompt,
        re.DOTALL
    )

    if not contextual_data_match:
        return task_prompt

    try:
        contextual_data = json.loads(contextual_data_match.group(1))
    except json.JSONDecodeError:
        return task_prompt

    local_files = []
    for item in contextual_data:
        if 'local_path' in item:
            local_files.append(item['local_path'])

    if not local_files:
        return task_prompt

    file_list = "\n".join([f"- {f}" for f in local_files])
    enhancement = f"\n\nThe following data files are available in your current working directory:\n{file_list}\n\nUse these local filenames to access the data.\n"

    parts = task_prompt.split('<ContextualNodeData>')
    if len(parts) == 2:
        return parts[0] + enhancement + '<ContextualNodeData>' + parts[1]

    return task_prompt
