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
