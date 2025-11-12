from spatialbench.graders.base import BinaryGrader, GraderResult
from spatialbench.types import TestResult

class LabelSetJaccardGrader(BinaryGrader):
    def evaluate(self, test_result: TestResult, config: dict) -> GraderResult:
        ground_truth_labels = set(config.get("ground_truth_labels", []))
        scoring = config.get("scoring", {})
        pass_threshold = scoring.get("pass_threshold", 0.90)

        agent_answer = self.extract_answer_from_tags(test_result.conversation_history)

        if agent_answer is None:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Agent did not provide answer in <EVAL_ANSWER> tags",
                agent_answer=None
            )

        if "cell_types_predicted" not in agent_answer:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Agent answer missing required field: cell_types_predicted",
                agent_answer=agent_answer
            )

        predicted_labels = set(agent_answer["cell_types_predicted"])

        intersection = ground_truth_labels & predicted_labels
        union = ground_truth_labels | predicted_labels

        jaccard_index = len(intersection) / len(union) if len(union) > 0 else 0.0

        passed = jaccard_index >= pass_threshold

        true_positives = intersection
        false_positives = predicted_labels - ground_truth_labels
        false_negatives = ground_truth_labels - predicted_labels

        metrics = {
            "jaccard_index": jaccard_index,
            "pass_threshold": pass_threshold,
            "true_positives": sorted(list(true_positives)),
            "false_positives": sorted(list(false_positives)),
            "false_negatives": sorted(list(false_negatives)),
            "predicted_count": len(predicted_labels),
            "ground_truth_count": len(ground_truth_labels),
        }

        reasoning = self._format_jaccard_reasoning(
            jaccard_index,
            pass_threshold,
            true_positives,
            false_positives,
            false_negatives,
            passed
        )

        return GraderResult(
            passed=passed,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_jaccard_reasoning(self, jaccard_index, threshold, true_positives, false_positives, false_negatives, passed):
        lines = []
        lines.append(f"Label Set Comparison: {'PASS' if passed else 'FAIL'}")
        lines.append("")
        lines.append(f"Jaccard Index: {jaccard_index:.3f} (threshold: {threshold:.3f}) {'✓' if jaccard_index >= threshold else '✗'}")
        lines.append("")

        if true_positives:
            lines.append(f"Correct Labels ({len(true_positives)}):")
            for label in sorted(true_positives):
                lines.append(f"  ✓ {label}")
        else:
            lines.append("Correct Labels: None")

        lines.append("")

        if false_positives:
            lines.append(f"Extra Labels ({len(false_positives)}):")
            for label in sorted(false_positives):
                lines.append(f"  + {label}")
        else:
            lines.append("Extra Labels: None")

        lines.append("")

        if false_negatives:
            lines.append(f"Missing Labels ({len(false_negatives)}):")
            for label in sorted(false_negatives):
                lines.append(f"  - {label}")
        else:
            lines.append("Missing Labels: None")

        lines.append("")
        lines.append(f"Result: {'PASS' if passed else 'FAIL'}")

        return "\n".join(lines)
