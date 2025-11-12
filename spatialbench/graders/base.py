import json
import re
from dataclasses import dataclass

from spatialbench.types import TestResult

@dataclass
class GraderResult:
    passed: bool
    metrics: dict
    reasoning: str
    agent_answer: dict | None

class BinaryGrader:
    def evaluate(self, test_result: TestResult, config: dict) -> GraderResult:
        agent_answer = self.extract_answer_from_tags(test_result.conversation_history)
        if agent_answer is None:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Failed to extract answer from conversation history",
                agent_answer=None
            )
        return self.evaluate_answer(agent_answer, config)

    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        raise NotImplementedError

    def extract_answer_from_tags(self, conversation: list[dict]) -> dict | None:
        for msg in reversed(conversation):
            if msg.get("type") != "anthropic_message" or msg.get("role") != "assistant":
                continue

            content = msg.get("content", [])
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if block.get("name") == "submit_response":
                        tool_input = block.get("input", {})
                        summary = tool_input.get("summary", "")

                        match = re.search(r'<EVAL_ANSWER>(.*?)</EVAL_ANSWER>', summary, re.DOTALL)
                        if match:
                            json_str = match.group(1).strip()
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError as e:
                                print(f"[grader] Failed to parse JSON from EVAL_ANSWER tags: {e}")
                                return None
        return None
