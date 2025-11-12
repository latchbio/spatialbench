import io
import json
import os
import re
import sys
from pathlib import Path

def run_minisweagent_task(
    task_prompt: str,
    work_dir: Path,
    model_name: str | None = None,
    agent_config: dict | None = None,
) -> dict:
    from minisweagent.agents.default import DefaultAgent
    from minisweagent.environments.local import LocalEnvironment
    from minisweagent.models import get_model

    original_dir = os.getcwd()

    captured_output = io.StringIO()
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    class TeeOutput:
        def __init__(self, *streams):
            self.streams = streams

        def write(self, data):
            for stream in self.streams:
                stream.write(data)
                stream.flush()

        def flush(self):
            for stream in self.streams:
                stream.flush()

    try:
        os.chdir(str(work_dir))

        sys.stdout = TeeOutput(original_stdout, captured_output)
        sys.stderr = TeeOutput(original_stderr, captured_output)

        enhanced_prompt = _enhance_prompt_with_local_files(task_prompt, work_dir)

        model = get_model(model_name)
        env = LocalEnvironment()

        if agent_config:
            agent = DefaultAgent(model, env, **agent_config)
        else:
            agent = DefaultAgent(model, env)

        try:
            agent.run(enhanced_prompt)
        except Exception as e:
            if "Submitted" in str(type(e).__name__):
                pass
            else:
                raise
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            agent_log_file = work_dir / "agent_output.log"
            agent_log_file.write_text(captured_output.getvalue())
            print(f"Agent output saved to: {agent_log_file}")

            if hasattr(agent, "messages"):
                trajectory_file = work_dir / "trajectory.json"
                trajectory_data = {
                    "messages": agent.messages,
                    "actions": getattr(agent, "actions", [])
                }
                trajectory_file.write_text(json.dumps(trajectory_data, indent=2))
                print(f"Agent trajectory saved to: {trajectory_file}")
                print(f"  Total message exchanges: {len(agent.messages)}")

        eval_answer_file = work_dir / "eval_answer.json"
        if not eval_answer_file.exists():
            raise FileNotFoundError(
                f"Agent did not create eval_answer.json in {work_dir}. "
                "Ensure the agent completes the task and writes the answer file."
            )

        try:
            agent_answer = json.loads(eval_answer_file.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse eval_answer.json: {e}. "
                f"File contents: {eval_answer_file.read_text()[:500]}"
            )

        return agent_answer

    finally:
        os.chdir(original_dir)

def _enhance_prompt_with_local_files(task_prompt: str, work_dir: Path) -> str:
    contextual_data_match = re.search(r'<ContextualNodeData>(.*?)</ContextualNodeData>', task_prompt, re.DOTALL)

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
