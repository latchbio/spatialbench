from spatialbench.graders.base import BinaryGrader, GraderResult

class NumericToleranceGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        ground_truth = config.get("ground_truth", {})
        tolerances = config.get("tolerances", {})

        metrics = {}
        all_pass = True
        failures = []

        for field, expected_value in ground_truth.items():
            if field not in agent_answer:
                all_pass = False
                failures.append(f"Missing field: {field}")
                continue

            actual_value = agent_answer[field]
            tolerance_config = tolerances.get(field, {"type": "absolute", "value": 0})
            tolerance_type = tolerance_config.get("type", "absolute")
            tolerance_value = tolerance_config.get("value", 0)

            if tolerance_type == "absolute":
                within_tolerance = abs(actual_value - expected_value) <= tolerance_value
                error = abs(actual_value - expected_value)
            elif tolerance_type == "relative":
                relative_error = abs(actual_value - expected_value) / abs(expected_value) if expected_value != 0 else float('inf')
                within_tolerance = relative_error <= tolerance_value
                error = relative_error
            elif tolerance_type == "min":
                within_tolerance = actual_value >= expected_value
                error = expected_value - actual_value if actual_value < expected_value else 0
            elif tolerance_type == "max":
                within_tolerance = actual_value <= expected_value
                error = actual_value - expected_value if actual_value > expected_value else 0
            else:
                within_tolerance = False
                error = float('inf')

            metrics[f"{field}_actual"] = actual_value
            metrics[f"{field}_expected"] = expected_value
            metrics[f"{field}_error"] = error
            metrics[f"{field}_pass"] = within_tolerance

            if not within_tolerance:
                all_pass = False
                if tolerance_type == "min":
                    failures.append(f"{field}: {actual_value} (minimum required: {expected_value})")
                elif tolerance_type == "max":
                    failures.append(f"{field}: {actual_value} (maximum allowed: {expected_value})")
                else:
                    failures.append(f"{field}: {actual_value} vs {expected_value} (error: {error:.2f}, tolerance: {tolerance_value})")

        reasoning = self._format_numeric_reasoning(ground_truth, tolerances, agent_answer, metrics, failures, all_pass)

        return GraderResult(
            passed=all_pass,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_numeric_reasoning(self, ground_truth, tolerances, agent_answer, metrics, failures, passed):
        lines = []
        lines.append(f"Numeric Tolerance Check: {'PASS' if passed else 'FAIL'}")
        lines.append("")

        for field in ground_truth.keys():
            if f"{field}_actual" in metrics:
                actual = metrics[f"{field}_actual"]
                expected = metrics[f"{field}_expected"]
                error = metrics[f"{field}_error"]
                field_pass = metrics[f"{field}_pass"]
                check = "✓" if field_pass else "✗"
                tolerance_config = tolerances.get(field, {})
                tolerance_type = tolerance_config.get("type", "absolute")
                if tolerance_type == "min":
                    lines.append(f"- {field}: {actual} (minimum: {expected}) {check}")
                elif tolerance_type == "max":
                    lines.append(f"- {field}: {actual} (maximum: {expected}) {check}")
                else:
                    lines.append(f"- {field}: {actual} vs {expected} (error: {error:.2f}) {check}")

        if not passed:
            lines.append("")
            lines.append("Failures:")
            for failure in failures:
                lines.append(f"  - {failure}")

        return "\n".join(lines)
