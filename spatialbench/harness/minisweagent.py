import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

class StreamingLogFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.buffer = io.StringIO()

    def write(self, data):
        self.buffer.write(data)
        with open(self.file_path, 'a') as f:
            f.write(data)
            f.flush()

    def flush(self):
        pass

    def getvalue(self):
        return self.buffer.getvalue()

def _patch_agent_for_progress(log_file, agent_class):
    original_add_message = agent_class.add_message

    def patched_add_message(self, role, content, **kwargs):
        original_add_message(self, role, content, **kwargs)

        with open(log_file, 'a') as f:
            if role == "assistant":
                step_num = len([m for m in self.messages if m.get("role") == "assistant"])
                f.write(f"\n[Step {step_num}]\n")
                f.write(f"Assistant: {content}\n")
            elif role == "user" and len(self.messages) > 2:
                f.write(f"Observation: {content}\n")
            f.flush()

    agent_class.add_message = patched_add_message

def run_minisweagent_task(
    task_prompt: str,
    work_dir: Path,
    model_name: str | None = None,
    agent_config: dict | None = None,
    timeout: int = 1200,
) -> dict:
    from minisweagent.agents.default import DefaultAgent, AgentConfig, FormatError
    from minisweagent.environments.local import LocalEnvironment
    from minisweagent.models import get_model
    import re

    class FlexibleAgent(DefaultAgent):
        def parse_action(self, response: dict) -> dict:
            content = response["content"]
            actions = re.findall(r"```(?:bash|sh|shell)?\s*\n(.*?)\n?```", content, re.DOTALL)
            if len(actions) == 1:
                return {"action": actions[0].strip(), **response}
            raise FormatError(self.render_template(self.config.format_error_template, actions=actions))

        def has_finished(self, output: dict):
            from minisweagent.agents.default import Submitted
            full_output = output.get("output", "")
            for marker in ["COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT", "MINI_SWE_AGENT_FINAL_OUTPUT"]:
                if marker in full_output:
                    idx = full_output.find(marker)
                    rest = full_output[idx + len(marker):].strip()
                    raise Submitted(rest)

    original_dir = os.getcwd()

    agent_log_file = work_dir / "agent_output.log"
    _patch_agent_for_progress(agent_log_file, FlexibleAgent)
    if agent_log_file.exists():
        agent_log_file.unlink()

    captured_output = StreamingLogFile(agent_log_file)
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    class TeeOutput:
        def __init__(self, *streams):
            self.streams = streams

        def write(self, data):
            for stream in self.streams:
                stream.write(data)
                if hasattr(stream, 'flush'):
                    stream.flush()

        def flush(self):
            for stream in self.streams:
                if hasattr(stream, 'flush'):
                    stream.flush()

    agent = None
    try:
        os.chdir(str(work_dir))

        sys.stdout = TeeOutput(original_stdout, captured_output)
        sys.stderr = TeeOutput(original_stderr, captured_output)

        enhanced_prompt = _enhance_prompt_with_local_files(task_prompt, work_dir)

        if model_name:
            os.environ['MSWEA_MODEL_NAME'] = model_name

        model = get_model()
        env = LocalEnvironment(timeout=1800)

        if agent_config:
            agent = FlexibleAgent(model, env, step_limit=100, **agent_config)
        else:
            agent = FlexibleAgent(model, env, step_limit=100)

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
        agent_answer = None
        error_details = None

        if not eval_answer_file.exists():
            agent_log_file = work_dir / "agent_output.log"
            log_tail = ""
            if agent_log_file.exists():
                log_content = agent_log_file.read_text()
                log_tail = log_content[-1000:]

            trajectory_info = ""
            if hasattr(agent, "messages"):
                trajectory_info = f"Agent had {len(agent.messages)} message exchanges."

            error_details = {
                "error": "Agent did not create eval_answer.json",
                "trajectory_info": trajectory_info,
                "log_tail": log_tail
            }
            print(f"\nWarning: Agent did not create eval_answer.json. {trajectory_info}")
        else:
            try:
                agent_answer = json.loads(eval_answer_file.read_text())
            except json.JSONDecodeError as e:
                error_details = {
                    "error": f"Failed to parse eval_answer.json: {e}",
                    "file_contents": eval_answer_file.read_text()[:500]
                }
                print(f"\nWarning: Failed to parse eval_answer.json: {e}")

        metadata = {}
        if hasattr(agent, "model"):
            metadata["total_cost"] = getattr(agent.model, "cost", None)
            metadata["n_steps"] = getattr(agent.model, "n_calls", None)
        if hasattr(agent, "messages"):
            metadata["n_messages"] = len(agent.messages)
        if error_details:
            metadata["error_details"] = error_details

        return {"answer": agent_answer, "metadata": metadata}

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
