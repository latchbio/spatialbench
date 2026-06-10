import argparse
import json
from pathlib import Path

import pandas as pd
from dataclasses import dataclass
from datetime import datetime

MILLION = 1_000_000


@dataclass
class ResultTableRow:
    task_file_name: str
    task_id: str
    model_name: str
    harness: str
    trial: int
    passed: bool
    steps: int
    duration_s: float
    execution_s: float
    cost: float


@dataclass
class TrialData:
    passed: bool
    steps: int
    duration_s: float
    execution_s: float
    cost: float


# we only lay out costs for OAI/Anthropic models because when using Codex/ClaudeCode we calculate costs from tokens. When using mini-swe-agent we get cost from the mini-swe harness.
cost_table = {
    "anthropic/claude-sonnet-4-5": {
        "input_tokens": 3 / MILLION,
        "output_tokens": 15 / MILLION,
        "ephemeral_5m_input_tokens": 3.75 / MILLION,
        "ephemeral_1h_input_tokens": 6 / MILLION,
        "cache_read_input_tokens": 0.30 / MILLION,
    },
    "anthropic/claude-sonnet-4-6": {
        "input_tokens": 3 / MILLION,
        "output_tokens": 15 / MILLION,
        "ephemeral_5m_input_tokens": 3.75 / MILLION,
        "ephemeral_1h_input_tokens": 6 / MILLION,
        "cache_read_input_tokens": 0.30 / MILLION,
    },
    "anthropic/claude-opus-4-5": {
        "input_tokens": 5 / MILLION,
        "output_tokens": 25 / MILLION,
        "ephemeral_5m_input_tokens": 6.25 / MILLION,
        "ephemeral_1h_input_tokens": 10 / MILLION,
        "cache_read_input_tokens": 0.50 / MILLION,
    },
    "anthropic/claude-opus-4-6": {
        "input_tokens": 5 / MILLION,
        "output_tokens": 25 / MILLION,
        "ephemeral_5m_input_tokens": 6.25 / MILLION,
        "ephemeral_1h_input_tokens": 10 / MILLION,
        "cache_read_input_tokens": 0.50 / MILLION,
    },
    "anthropic/claude-opus-4-7": {
        "input_tokens": 5 / MILLION,
        "output_tokens": 25 / MILLION,
        "ephemeral_5m_input_tokens": 6.25 / MILLION,
        "ephemeral_1h_input_tokens": 10 / MILLION,
        "cache_read_input_tokens": 0.50 / MILLION,
    },
    "anthropic/claude-opus-4-1": {
        "input_tokens": 15 / MILLION,
        "output_tokens": 75 / MILLION,
        "ephemeral_5m_input_tokens": 18.75 / MILLION,
        "ephemeral_1h_input_tokens": 30 / MILLION,
        "cache_read_input_tokens": 1.50 / MILLION,
    },
    "openai/gpt-5.2": {
        "input_tokens": 1.75 / MILLION,
        "output_tokens": 14 / MILLION,
        "cached_tokens": 0.175 / MILLION,
    },
    "openai/gpt-5.1": {
        "input_tokens": 1.25 / MILLION,
        "output_tokens": 10 / MILLION,
        "cached_tokens": 0.125 / MILLION,
    },
    "openai/gpt-5.3-codex": {
        "input_tokens": 1.75 / MILLION,
        "output_tokens": 14 / MILLION,
        "cached_tokens": 0.175 / MILLION,
    },
    "openai/gpt-5.4": {
        "input_tokens": 2.50 / MILLION,
        "output_tokens": 15 / MILLION,
        "cached_tokens": 0.25 / MILLION,
    },
    "openai/gpt-5.5": {
        "input_tokens": 5 / MILLION,
        "output_tokens": 30 / MILLION,
        "cached_tokens": 0.5 / MILLION,
    },
}


def calculate_miniswe_execution_seconds(
    model_name: str, trajectory_json: dict
) -> float:
    messages = trajectory_json["messages"]
    execution_seconds = 0.0
    last_model_ts = None

    for msg in messages:
        extra = msg.get("extra")
        if not isinstance(extra, dict) or "timestamp" not in extra:
            continue

        ts = extra["timestamp"]

        is_model = msg.get("role") == "assistant" or msg.get("object") == "response"
        is_exec = msg.get("role") == "tool" or msg.get("type") == "function_call_output"

        if is_model:
            last_model_ts = ts
        elif is_exec and last_model_ts is not None:
            execution_seconds += ts - last_model_ts
            last_model_ts = ts

    return execution_seconds


def get_mini_swe_data(model: str, harness: str, trial_dir: Path) -> TrialData:
    results_json = json.loads((trial_dir / "result.json").read_text())
    passed = results_json["result"]["passed"]
    n_steps = results_json["result"]["metadata"]["n_steps"]
    duration_s = results_json["agent_runtime_seconds"]
    cost = results_json["result"]["metadata"]["total_cost"]
    # To calculate execution seconds use timestamp diffs between responses and model message timestamps
    trajectory_json = json.loads((trial_dir / "trajectory.json").read_text())
    execution_s = calculate_miniswe_execution_seconds(model, trajectory_json)
    return TrialData(
        passed=passed,
        steps=n_steps,
        duration_s=duration_s,
        execution_s=execution_s,
        cost=cost,
    )


def calculate_claude_code_execution_seconds(entries: list[dict]) -> float:
    """Model time = total session duration - tool execution time.

    Tool execution time is measured as intervals from the last assistant
    message (tool_use) to the subsequent user message carrying a tool_result.
    """
    tool_exec_seconds = 0.0
    last_assistant_ts = None
    first_ts = None
    last_ts = None

    for entry in entries:
        ts_str = entry.get("timestamp")
        if not ts_str:
            continue
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if first_ts is None:
            first_ts = ts
        last_ts = ts

        entry_type = entry.get("type")
        if entry_type == "assistant":
            last_assistant_ts = ts
        elif entry_type == "user" and last_assistant_ts is not None:
            content = entry.get("message", {}).get("content", [])
            has_tool_result = any(
                isinstance(c, dict) and c.get("type") == "tool_result"
                for c in (content if isinstance(content, list) else [])
            )
            if has_tool_result:
                tool_exec_seconds += (ts - last_assistant_ts).total_seconds()
            last_assistant_ts = None

    if first_ts is None or last_ts is None:
        return 0.0
    return (last_ts - first_ts).total_seconds() - tool_exec_seconds


def get_claude_code_data(model: str, harness: str, trial_dir: Path) -> TrialData:
    results_json = json.loads((trial_dir / "result.json").read_text())
    passed = results_json["result"]["passed"]
    duration_s = results_json["agent_runtime_seconds"]

    entries = [
        json.loads(line)
        for line in (trial_dir / "harness_outputs.jsonl").read_text().splitlines()
        if line.strip()
    ]

    # Multiple assistant entries share a requestId (streaming chunks).
    # Keep only the last per requestId to get final token usage.
    final_by_request: dict[str, dict] = {}
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        req_id = entry.get("requestId")
        if req_id:
            final_by_request[req_id] = entry

    total_input_tokens = 0
    total_output_tokens = 0
    total_ephemeral_5m = 0
    total_ephemeral_1h = 0
    total_cache_read = 0

    for entry in final_by_request.values():
        usage = entry.get("message", {}).get("usage", {})
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)
        total_cache_read += usage.get("cache_read_input_tokens", 0)
        cache_creation = usage.get("cache_creation", {})
        total_ephemeral_5m += cache_creation.get("ephemeral_5m_input_tokens", 0)
        total_ephemeral_1h += cache_creation.get("ephemeral_1h_input_tokens", 0)

    steps = len(final_by_request)

    rates = cost_table[f"anthropic/{model}"]
    cost = (
        total_input_tokens * rates["input_tokens"]
        + total_output_tokens * rates["output_tokens"]
        + total_ephemeral_5m * rates["ephemeral_5m_input_tokens"]
        + total_ephemeral_1h * rates["ephemeral_1h_input_tokens"]
        + total_cache_read * rates["cache_read_input_tokens"]
    )

    execution_s = calculate_claude_code_execution_seconds(entries)

    return TrialData(
        passed=passed,
        steps=steps,
        duration_s=duration_s,
        execution_s=execution_s,
        cost=cost,
    )


def calculate_codex_execution_seconds(entries: list[dict]) -> float:
    """Model time = total session duration - tool execution time.

    Tool execution time is measured as intervals from response_item function_call
    to the subsequent response_item function_call_output.
    """
    tool_exec_seconds = 0.0
    last_call_ts = None
    first_ts = None
    last_ts = None

    for entry in entries:
        ts_str = entry.get("timestamp")
        if not ts_str:
            continue
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if first_ts is None:
            first_ts = ts
        last_ts = ts

        if entry.get("type") == "response_item":
            ptype = entry.get("payload", {}).get("type")
            if ptype == "function_call":
                last_call_ts = ts
            elif ptype == "function_call_output" and last_call_ts is not None:
                tool_exec_seconds += (ts - last_call_ts).total_seconds()
                last_call_ts = None

    if first_ts is None or last_ts is None:
        return 0.0
    return (last_ts - first_ts).total_seconds() - tool_exec_seconds


def get_openai_codex_data(
    model_name: str, harness_name: str, trial_dir: Path
) -> TrialData:
    results_json = json.loads((trial_dir / "result.json").read_text())
    passed = results_json["result"]["passed"]
    duration_s = results_json["agent_runtime_seconds"]

    entries = [
        json.loads(line)
        for line in (trial_dir / "harness_outputs.jsonl").read_text().splitlines()
        if line.strip()
    ]

    # Extract final cumulative token usage from the last token_count event
    last_usage = None
    for entry in entries:
        if entry.get("type") == "event_msg":
            payload = entry.get("payload", {})
            if payload.get("type") == "token_count":
                last_usage = payload["info"]["total_token_usage"]
    usage = last_usage or {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
    }

    cached = usage.get("cached_input_tokens", 0)
    base_input = usage["input_tokens"] - cached
    rates = cost_table[f"openai/{model_name}"]
    cost = (
        base_input * rates["input_tokens"]
        + cached * rates["cached_tokens"]
        + usage["output_tokens"] * rates["output_tokens"]
    )

    steps = sum(
        1
        for e in entries
        if e.get("type") == "response_item"
        and e.get("payload", {}).get("type") == "function_call"
    )

    execution_s = calculate_codex_execution_seconds(entries)

    return TrialData(
        passed=passed,
        steps=steps,
        duration_s=duration_s,
        execution_s=execution_s,
        cost=cost,
    )


def build_results_table(
    evals_dir: Path, trajectories_dir: Path, results_file_path: Path
):
    # First get all evals
    eval_task_files = evals_dir.rglob("*.json")

    results_table_rows: list[ResultTableRow] = []
    # Trajectories dir has format: <task_file_name>/<provider>/<model>/<harness>/<trial>/<trajectory>.json
    try:
        for eval_task_file in eval_task_files:
            eval_task_results_dir = trajectories_dir / eval_task_file.stem
            for trial_dir in sorted(eval_task_results_dir.glob("*/*/*/*")):
                if not trial_dir.is_dir():
                    print(f"Skipping {trial_dir} because it is not a directory")
                    continue
                provider, model, harness, trial_name = trial_dir.relative_to(
                    eval_task_results_dir
                ).parts
                trial_index = int(trial_name[1:])
                match harness:
                    case "mini-swe-agent":
                        trial_data = get_mini_swe_data(model, harness, trial_dir)
                    case "claude-code":
                        trial_data = get_claude_code_data(model, harness, trial_dir)
                    case "openai-codex":
                        trial_data = get_openai_codex_data(model, harness, trial_dir)
                    case _:
                        raise ValueError(f"Unknown harness: {harness}")
                results_table_rows.append(
                    ResultTableRow(
                        task_file_name=eval_task_file.name,
                        task_id=json.loads(eval_task_file.read_text())["id"],
                        model_name=model,
                        harness=harness,
                        trial=trial_index,
                        passed=trial_data.passed,
                        steps=trial_data.steps,
                        duration_s=trial_data.duration_s,
                        execution_s=trial_data.execution_s,
                        cost=trial_data.cost,
                    )
                )
        df = pd.DataFrame(results_table_rows)
        results_file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(results_file_path, index=False)
    except Exception as e:
        print(f"Error generating results table: {e}")
        raise e


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark results table")
    parser.add_argument(
        "--evals",
        type=Path,
        help="Directory containing evaluation JSON files",
        required=True,
    )
    parser.add_argument(
        "--trajectories",
        type=Path,
        help="Directory containing trajectory files",
        required=True,
    )
    parser.add_argument(
        "--results", type=Path, help="Path to save results table", required=True
    )
    args = parser.parse_args()

    build_results_table(Path(args.evals), Path(args.trajectories), Path(args.results))


if __name__ == "__main__":
    main()
