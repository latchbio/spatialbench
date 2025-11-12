# Contributing to SpatialBench

Thank you for your interest in contributing to SpatialBench! This document provides guidelines for creating custom graders and submitting benchmark results.

**Note**: This repository contains example evaluations only. The full 98-evaluation benchmark is maintained separately to prevent overfitting. Contact [kenny@latch.bio](mailto:kenny@latch.bio) for information about contributing to the full benchmark.

## Table of Contents

1. [Creating a Custom Grader](#creating-a-custom-grader)
2. [Submitting Benchmark Results](#submitting-benchmark-results)
3. [Code Style](#code-style)

## Full Benchmark Information

The complete SpatialBench comprises **98 evaluations** across four platforms:

| Technology       | Evaluations |
|------------------|-------------|
| Xenium           | 30          |
| Vizgen (MERFISH) | 31          |
| AtlasXomics      | 25          |
| Seeker/Curio     | 12          |
| **Total**        | **98**      |

This repository contains 7 representative examples. The full benchmark is withheld to ensure performance metrics reflect genuine spatial biology capabilities.

## Creating a Custom Grader

### Prerequisites

- Python 3.10+
- Familiarity with spatial biology analysis
- Access to spatial transcriptomics/epigenomics datasets

### Step-by-Step Guide

#### 1. Identify the Task

Choose a spatial biology analysis task that:
- Represents a real-world analysis workflow
- Has a clear, reproducible ground truth
- Tests specific agent capabilities (biological reasoning, statistical analysis, etc.)

#### 2. Prepare Ground Truth

Run the analysis manually using standard tools (scanpy, Seurat, etc.) to establish ground truth:

```python
import scanpy as sc

adata = sc.read_h5ad("dataset.h5ad")
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

ground_truth = {
    "mean_sum_per_cell": float(adata.X.sum(axis=1).mean()),
    "max_value": float(adata.X.max()),
    "min_value": float(adata.X.min())
}
```

**Best Practices**:
- Document all parameters and random seeds
- Use canonical methods from published papers
- Validate reproducibility by running multiple times
- Include references to relevant papers/protocols

#### 3. Choose Appropriate Grader(s)

Select grader(s) that match your evaluation criteria:

| Grader | Use Case | Example |
|--------|----------|---------|
| NumericToleranceGrader | Numeric metrics (counts, percentages) | QC metrics, gene counts |
| LabelSetJaccardGrader | Set comparison | Cell type vocabularies |
| DistributionComparisonGrader | Proportions/percentages | Cell type distributions |
| MarkerGenePrecisionRecallGrader | Ranked lists | Top-K marker genes |
| MarkerGeneSeparationGrader | Expression validation | AUROC for markers |
| SpatialAdjacencyGrader | Spatial metrics | Cell-cell distances |

See [docs/graders.md](docs/graders.md) for detailed documentation.

#### 4. Write Eval JSON

Create a JSON file following the specification:

```json
{
  "id": "platform_task_description_v1",
  "task": "Clear task description with expected output format...",
  "data_node": "latch://path/to/dataset.h5ad",
  "grader": {
    "type": "grader_name",
    "config": {
      "ground_truth": {...},
      "tolerances": {...}
    }
  }
}
```

**Task Description Guidelines**:
- Be specific about expected output format
- Include exact field names for JSON output
- Specify any analysis parameters (e.g., "Use Leiden clustering with resolution=1.0")
- Provide biological context when relevant

#### 5. Test Locally

Test your evaluation before submitting:

```python
from spatialbench import EvalRunner

runner = EvalRunner("my_new_eval.json", keep_workspace=True)
result = runner.run(agent_function=my_test_agent)
```

Verify:
- Ground truth is achievable
- Grader passes with correct answers
- Grader fails with incorrect answers
- Task description is unambiguous

#### 6. Document

Add your evaluation to `evals/README.md`:

```markdown
### Task Category

**Eval ID**: `platform_task_v1`
**Platform**: Xenium/AtlasXomics/Vizgen/Seeker
**Task**: Brief description
**Grader**: grader_name
**Difficulty**: Easy/Medium/Hard
```

#### 7. Submit Pull Request

Submit a PR with:
- [ ] Eval JSON file in appropriate category folder
- [ ] Updated evals/README.md
- [ ] Test results showing the eval works
- [ ] Any relevant references or documentation

**PR Template**:
```markdown
## New Evaluation: [Eval ID]

**Category**: QC/Preprocessing/Clustering/Cell Typing/DE/Spatial

**Description**: Brief description of what this eval tests

**Ground Truth Method**: How ground truth was established

**Testing**: Confirm eval passes with correct answers and fails with incorrect ones

**References**: Links to relevant papers/protocols
```

## Creating a Custom Grader

If none of the built-in graders fit your needs, create a custom one:

### 1. Subclass BinaryGrader

```python
from spatialbench.graders.base import BinaryGrader, GraderResult

class MyCustomGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        ground_truth = config.get("ground_truth")

        passed = True
        metrics = {}
        failures = []

        if agent_answer.get("some_field") != ground_truth:
            passed = False
            failures.append("Field mismatch")

        reasoning = self._format_reasoning(passed, failures)

        return GraderResult(
            passed=passed,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )

    def _format_reasoning(self, passed, failures):
        lines = []
        lines.append(f"Custom Grader: {'PASS' if passed else 'FAIL'}")
        if failures:
            lines.append("Failures:")
            for f in failures:
                lines.append(f"  - {f}")
        return "\n".join(lines)
```

### 2. Write Unit Tests

```python
def test_custom_grader():
    grader = MyCustomGrader()

    agent_answer = {"some_field": "value"}
    config = {"ground_truth": "value"}

    result = grader.evaluate_answer(agent_answer, config)
    assert result.passed

    agent_answer = {"some_field": "wrong"}
    result = grader.evaluate_answer(agent_answer, config)
    assert not result.passed
```

### 3. Register Grader

Add to `spatialbench/graders/__init__.py`:

```python
from spatialbench.graders.my_custom import MyCustomGrader

GRADER_REGISTRY = {
    ...
    "my_custom": MyCustomGrader,
}
```

### 4. Document

Add to `docs/graders.md` with:
- Description of what it evaluates
- Config schema
- Example usage
- When to use it

### 5. Submit PR

Include:
- [ ] Grader implementation
- [ ] Unit tests
- [ ] Documentation in docs/graders.md
- [ ] Registry update
- [ ] Example evaluation using the grader

## Submitting Benchmark Results

Help build the leaderboard by benchmarking your model:

### 1. Run Benchmark

```bash
spatialbench batch evals/ --model your-model-name --output results/
```

### 2. Generate Summary

```bash
spatialbench leaderboard results/ --output summary.json
```

### 3. Submit PR

Include:
- [ ] summary.json with results
- [ ] Model name and version
- [ ] Date of evaluation
- [ ] Any relevant notes (hardware, runtime, etc.)

## Code Style

### Python

- End files with newlines
- No docstrings or comments (per project style)
- Use `|` for Union types: `str | None`
- Imports at top of file
- Use available types (`list`, `dict`) instead of typing module

### JSON

- 2-space indentation
- No trailing commas
- Sorted keys (for ground truth labels)

### Commits

- Clear, descriptive commit messages
- One logical change per commit
- Reference issue numbers when applicable

## Review Process

1. **Automated checks**: Tests and linting must pass
2. **Ground truth review**: Verify analysis is correct and reproducible
3. **Grader review**: Ensure grader logic is sound
4. **Documentation review**: Check clarity and completeness
5. **Approval**: Two maintainer approvals required

## Questions?

- Open an issue for questions
- Tag maintainers for urgent reviews
- Join discussions for design decisions

Thank you for contributing to SpatialBench!
