from spatialbench.graders.base import BinaryGrader, GraderResult


class MultipleChoiceGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        correct_answer = config.get("correct_answer", "").strip().upper()

        if "answer" not in agent_answer:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Agent answer missing required field: answer",
                agent_answer=agent_answer
            )

        agent_choice = str(agent_answer["answer"]).strip().upper()

        passed = agent_choice == correct_answer

        metrics = {
            "correct_answer": correct_answer,
            "agent_answer": agent_choice,
        }

        reasoning = self._format_reasoning(correct_answer, agent_choice, passed)

        return GraderResult(
            passed=passed,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_reasoning(self, correct, agent, passed):
        lines = []
        lines.append(f"Multiple Choice: {'PASS' if passed else 'FAIL'}")
        lines.append("")
        if passed:
            lines.append(f"✓ Agent answered: {agent} (correct)")
        else:
            lines.append(f"✗ Agent answered: {agent}")
            lines.append(f"  Correct answer: {correct}")
        return "\n".join(lines)
