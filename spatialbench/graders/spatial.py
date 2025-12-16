from spatialbench.graders.base import BinaryGrader, GraderResult

class SpatialAdjacencyGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        scoring = config.get("scoring", {})
        thresholds = scoring.get("pass_thresholds", {})

        max_median_ic_to_pc = thresholds.get("max_median_ic_to_pc_um", 25.0)
        max_p90_ic_to_pc = thresholds.get("max_p90_ic_to_pc_um", 80.0)
        min_pct_within_15um = thresholds.get("min_pct_ic_within_15um", 60.0)
        min_pct_mixed_within_55um = thresholds.get("min_pct_ic_mixed_within_55um", 60.0)

        required_fields = [
            "median_ic_to_pc_um",
            "p90_ic_to_pc_um",
            "pct_ic_within_15um",
            "pct_ic_mixed_within_55um",
            "adjacency_pass"
        ]

        missing = [f for f in required_fields if f not in agent_answer]
        if missing:
            return GraderResult(
                passed=False,
                metrics={},
                reasoning=f"Agent answer missing required fields: {missing}",
                agent_answer=agent_answer
            )

        median_ic_to_pc = agent_answer["median_ic_to_pc_um"]
        p90_ic_to_pc = agent_answer["p90_ic_to_pc_um"]
        pct_within_15um = agent_answer["pct_ic_within_15um"]
        pct_mixed_within_55um = agent_answer["pct_ic_mixed_within_55um"]
        adjacency_pass = agent_answer["adjacency_pass"]

        median_pass = median_ic_to_pc <= max_median_ic_to_pc
        p90_pass = p90_ic_to_pc <= max_p90_ic_to_pc
        within_15um_pass = pct_within_15um >= min_pct_within_15um
        mixed_55um_pass = pct_mixed_within_55um >= min_pct_mixed_within_55um

        passed = median_pass and p90_pass and within_15um_pass and mixed_55um_pass and adjacency_pass

        metrics = {
            "median_ic_to_pc_um": median_ic_to_pc,
            "p90_ic_to_pc_um": p90_ic_to_pc,
            "pct_ic_within_15um": pct_within_15um,
            "pct_ic_mixed_within_55um": pct_mixed_within_55um,
            "adjacency_pass": adjacency_pass,
            "max_median_threshold": max_median_ic_to_pc,
            "max_p90_threshold": max_p90_ic_to_pc,
            "min_pct_15um_threshold": min_pct_within_15um,
            "min_pct_55um_threshold": min_pct_mixed_within_55um,
            "median_pass": median_pass,
            "p90_pass": p90_pass,
            "within_15um_pass": within_15um_pass,
            "mixed_55um_pass": mixed_55um_pass,
        }

        reasoning = self._format_spatial_adjacency_reasoning(
            median_ic_to_pc,
            p90_ic_to_pc,
            pct_within_15um,
            pct_mixed_within_55um,
            adjacency_pass,
            max_median_ic_to_pc,
            max_p90_ic_to_pc,
            min_pct_within_15um,
            min_pct_mixed_within_55um,
            median_pass,
            p90_pass,
            within_15um_pass,
            mixed_55um_pass,
            passed
        )

        return GraderResult(
            passed=passed,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_spatial_adjacency_reasoning(self, median_dist, p90_dist, pct_15um, pct_55um,
                                           adjacency_pass, max_median, max_p90, min_15um, min_55um,
                                           median_pass, p90_pass, within_15_pass, mixed_55_pass, passed):
        lines = []
        lines.append(f"Spatial Adjacency Analysis: {'PASS' if passed else 'FAIL'}")
        lines.append("")

        lines.append("IC→PC Distance Metrics:")
        median_check = "✓" if median_pass else "✗"
        lines.append(f"  {median_check} Median distance: {median_dist:.2f} µm (threshold: ≤{max_median:.2f} µm)")

        p90_check = "✓" if p90_pass else "✗"
        lines.append(f"  {p90_check} 90th percentile: {p90_dist:.2f} µm (threshold: ≤{max_p90:.2f} µm)")

        lines.append("")
        lines.append("IC Proximity to PC:")
        within_15_check = "✓" if within_15_pass else "✗"
        lines.append(f"  {within_15_check} IC within 15 µm: {pct_15um:.1f}% (threshold: ≥{min_15um:.1f}%)")

        mixed_55_check = "✓" if mixed_55_pass else "✗"
        lines.append(f"  {mixed_55_check} IC with PC within 55 µm: {pct_55um:.1f}% (threshold: ≥{min_55um:.1f}%)")

        lines.append("")
        adjacency_check = "✓" if adjacency_pass else "✗"
        lines.append(f"Agent adjacency assessment: {adjacency_check} {adjacency_pass}")

        lines.append("")
        lines.append(f"Result: {'PASS' if passed else 'FAIL'}")
        if not passed:
            failures = []
            if not median_pass:
                failures.append(f"Median {median_dist:.2f} > {max_median:.2f} µm")
            if not p90_pass:
                failures.append(f"P90 {p90_dist:.2f} > {max_p90:.2f} µm")
            if not within_15_pass:
                failures.append(f"Within 15 µm {pct_15um:.1f}% < {min_15um:.1f}%")
            if not mixed_55_pass:
                failures.append(f"Within 55 µm {pct_55um:.1f}% < {min_55um:.1f}%")
            if not adjacency_pass:
                failures.append("Agent marked adjacency_pass as false")
            lines.append(f"Reasons: {'; '.join(failures)}")

        return "\n".join(lines)
