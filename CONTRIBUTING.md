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

Graders are maintained in a separate repository. To create a custom grader, see [eval-graders](https://github.com/latchbio/eval-graders).

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
