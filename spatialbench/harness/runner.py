import json
from pathlib import Path

from spatialbench.types import TestCase, TestResult, EvalResult
from eval_graders import GRADER_REGISTRY
from spatialbench.harness.utils import download_data, setup_workspace, cleanup_workspace

class EvalRunner:
    def __init__(self, eval_path: str | Path, keep_workspace: bool = False, run_id: str | None = None):
        self.eval_path = Path(eval_path)
        self.keep_workspace = keep_workspace
        self.run_id = run_id

        if not self.eval_path.exists():
            raise FileNotFoundError(f"Eval file not found: {self.eval_path}")

        eval_data = json.loads(self.eval_path.read_text())
        self.test_case = TestCase(**eval_data)

    def run(self, agent_function=None):
        print("=" * 80)
        print(f"Running SpatialBench evaluation: {self.test_case.id}")
        print("=" * 80)

        print("\nTask:")
        print("-" * 80)
        print(self.test_case.task)
        print("-" * 80)

        work_dir = setup_workspace(self.test_case.id, self.run_id)
        print(f"\nWorking directory: {work_dir}")

        print("\n" + "=" * 80)
        print("Staging data files...")
        print("=" * 80)

        contextual_data = download_data(self.test_case.data_node, work_dir)

        data_context = ""
        if contextual_data:
            data_context = f"\n\nHere is the context of the selected nodes the user would like to use: <ContextualNodeData>{json.dumps(contextual_data)}</ContextualNodeData>"

        task_prompt = f"""{self.test_case.task}

IMPORTANT: When you have completed this task:
1. Write your final answer as a JSON object to a file named `eval_answer.json`
2. The file should contain ONLY the JSON object with the required fields
3. After writing the file, you have completed the task

Example eval_answer.json:
{{
  "field1": value1,
  "field2": value2
}}
{data_context}"""

        print("\n" + "=" * 80)
        print("Running agent on task...")
        print("=" * 80)

        agent_answer = None
        agent_metadata = {}

        if agent_function is None:
            print("\nNo agent function provided. To run this eval, pass an agent_function that:")
            print("  1. Takes (task_prompt: str, work_dir: Path) as arguments")
            print("  2. Returns the parsed agent answer dict")
            print(f"\nExample:")
            print(f"  def my_agent(task, work_dir):")
            print(f"      # Run your agent")
            print(f"      # Agent should write eval_answer.json to work_dir")
            print(f"      answer_file = work_dir / 'eval_answer.json'")
            print(f"      return json.loads(answer_file.read_text())")
            print(f"\n  runner = EvalRunner(eval_path)")
            print(f"  runner.run(agent_function=my_agent)")
        else:
            try:
                result = agent_function(task_prompt, work_dir)

                if isinstance(result, dict) and "answer" in result:
                    agent_answer = result["answer"]
                    agent_metadata = result.get("metadata", {})
                else:
                    agent_answer = result

                print("\nAgent completed successfully")
            except Exception as e:
                print(f"\nAgent error: {e}")
                import traceback
                traceback.print_exc()

        eval_answer_path = work_dir / "eval_answer.json"
        if agent_answer is None and eval_answer_path.exists():
            try:
                agent_answer = json.loads(eval_answer_path.read_text())
                print(f"Loaded agent answer from eval_answer.json")
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse eval_answer.json: {e}")

        grader_result = None
        if self.test_case.grader and agent_answer is not None:
            print("\n" + "=" * 80)
            print("Running grader...")
            print("=" * 80)

            grader_type = self.test_case.grader.get("type")
            grader_config = self.test_case.grader.get("config", {})

            if grader_type in GRADER_REGISTRY:
                grader_cls = GRADER_REGISTRY[grader_type]
                grader = grader_cls()
                try:
                    grader_result = grader.evaluate_answer(agent_answer, grader_config)
                except Exception as e:
                    from eval_graders import GraderResult
                    import traceback
                    grader_result = GraderResult(
                        passed=False,
                        metrics={"grader_error": str(e)},
                        reasoning=f"Grader failed due to malformed agent output: {e}\n\n{traceback.format_exc()}",
                        agent_answer=agent_answer
                    )

                print(f"\n{'✓ EVAL PASSED' if grader_result.passed else '✗ EVAL FAILED'}")
                print("\nGrader reasoning:")
                print("-" * 80)
                print(grader_result.reasoning)
                print("-" * 80)

                if grader_result.metrics:
                    print("\nMetrics:")
                    for key, value in grader_result.metrics.items():
                        if isinstance(value, (list, dict)):
                            continue
                        print(f"   {key}: {value}")
            else:
                print(f"\nWarning: Unknown grader type '{grader_type}'")

        print("\n" + "=" * 80)
        print("Cleanup...")
        print("=" * 80)

        cleanup_workspace(work_dir, keep=self.keep_workspace)

        if self.keep_workspace:
            print(f"\nTo inspect results:")
            print(f"  cd {work_dir}")

        result_dict = {
            "test_id": self.test_case.id,
            "agent_answer": agent_answer,
            "grader_result": grader_result,
            "passed": grader_result.passed if grader_result else None,
        }

        if agent_metadata:
            result_dict["metadata"] = agent_metadata

        return result_dict
