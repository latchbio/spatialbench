from spatialbench.graders.base import BinaryGrader, GraderResult

class DistributionComparisonGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        ground_truth = config.get("ground_truth", {})
        tolerances = config.get("tolerances", {})

        gt_total_cells = ground_truth.get("total_cells")
        gt_distribution = ground_truth.get("cell_type_distribution", {})

        total_cells_tolerance = tolerances.get("total_cells", {})
        pct_tolerance_config = tolerances.get("cell_type_percentages", {})
        pct_tolerance = pct_tolerance_config.get("value", 3.0)

        if "total_cells" not in agent_answer:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Agent answer missing required field: total_cells",
                agent_answer=agent_answer
            )

        if "cell_type_distribution" not in agent_answer:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning="Agent answer missing required field: cell_type_distribution",
                agent_answer=agent_answer
            )

        agent_total_cells = agent_answer["total_cells"]
        agent_distribution = agent_answer["cell_type_distribution"]

        metrics = {}
        all_pass = True
        failures = []

        if gt_total_cells is not None:
            total_cells_tol_value = total_cells_tolerance.get("value", 0)
            total_cells_diff = abs(agent_total_cells - gt_total_cells)
            total_cells_pass = total_cells_diff <= total_cells_tol_value

            metrics["total_cells_actual"] = agent_total_cells
            metrics["total_cells_expected"] = gt_total_cells
            metrics["total_cells_diff"] = total_cells_diff
            metrics["total_cells_pass"] = total_cells_pass

            if not total_cells_pass:
                all_pass = False
                failures.append(f"total_cells: {agent_total_cells} vs {gt_total_cells} (diff: {total_cells_diff}, tolerance: {total_cells_tol_value})")

        distribution_failures = []
        for cell_type, expected_pct in gt_distribution.items():
            if cell_type not in agent_distribution:
                all_pass = False
                failures.append(f"Missing cell type: {cell_type}")
                distribution_failures.append(cell_type)
                metrics[f"{cell_type}_actual"] = None
                metrics[f"{cell_type}_expected"] = expected_pct
                metrics[f"{cell_type}_diff"] = None
                metrics[f"{cell_type}_pass"] = False
                continue

            actual_pct = agent_distribution[cell_type]
            diff = abs(actual_pct - expected_pct)
            within_tolerance = diff <= pct_tolerance

            metrics[f"{cell_type}_actual"] = actual_pct
            metrics[f"{cell_type}_expected"] = expected_pct
            metrics[f"{cell_type}_diff"] = diff
            metrics[f"{cell_type}_pass"] = within_tolerance

            if not within_tolerance:
                all_pass = False
                failures.append(f"{cell_type}: {actual_pct:.4f}% vs {expected_pct:.4f}% (diff: {diff:.4f}%, tolerance: {pct_tolerance}%)")
                distribution_failures.append(cell_type)

        extra_types = set(agent_distribution.keys()) - set(gt_distribution.keys())
        if extra_types:
            metrics["extra_cell_types"] = sorted(list(extra_types))
            failures.append(f"Extra cell types not in ground truth: {sorted(list(extra_types))}")

        reasoning = self._format_distribution_reasoning(
            agent_total_cells,
            gt_total_cells,
            metrics.get("total_cells_pass", True),
            gt_distribution,
            agent_distribution,
            pct_tolerance,
            distribution_failures,
            extra_types,
            failures,
            all_pass
        )

        return GraderResult(
            passed=all_pass,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_distribution_reasoning(self, agent_total, gt_total, total_pass,
                                       gt_distribution, agent_distribution, pct_tolerance,
                                       distribution_failures, extra_types, failures, passed):
        lines = []
        lines.append(f"Distribution Comparison: {'PASS' if passed else 'FAIL'}")
        lines.append("")

        if gt_total is not None:
            total_check = "✓" if total_pass else "✗"
            lines.append(f"Total cells: {agent_total} vs {gt_total} {total_check}")
            lines.append("")

        lines.append(f"Cell type percentages (tolerance: ±{pct_tolerance}%):")

        for cell_type in sorted(gt_distribution.keys()):
            expected = gt_distribution[cell_type]
            if cell_type not in agent_distribution:
                lines.append(f"  ✗ {cell_type}: MISSING vs {expected:.4f}%")
            else:
                actual = agent_distribution[cell_type]
                diff = abs(actual - expected)
                within_tol = diff <= pct_tolerance
                check = "✓" if within_tol else "✗"
                lines.append(f"  {check} {cell_type}: {actual:.4f}% vs {expected:.4f}% (diff: {diff:.4f}%)")

        if extra_types:
            lines.append("")
            lines.append(f"Extra cell types (not in ground truth): {sorted(list(extra_types))}")

        if not passed:
            lines.append("")
            lines.append("Failures:")
            for failure in failures:
                lines.append(f"  - {failure}")

        return "\n".join(lines)
