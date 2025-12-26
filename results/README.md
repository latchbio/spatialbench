# SpatialBench Results

Benchmark results from SpatialBench v2.0 evaluation (December 2025).

## Files

| File | Description |
|------|-------------|
| `benchmark_results.json` | Overall accuracy, cost, time, steps with 95% CIs |
| `results_by_task.json` | Accuracy by task category (7 categories, n=7-39 each) |
| `results_by_platform.json` | Accuracy by platform (5 platforms, n=18-43 each) |

## Methodology

- **Evaluations**: 146 total (145 with task-level CIs, 1 excluded for n=1)
- **Runs**: 3 independent runs per model
- **CI**: t-distribution 95% intervals over per-evaluation means

## Models

9 configurations: Claude Opus/Sonnet 4.5 (mini-swe-agent and Claude Code), GPT-5.1/5.2, Gemini 2.5 Pro, Grok-4/4.1 Fast Reasoning.

## Citation

```bibtex
@article{spatialbench2025,
  title = {SpatialBench: Can Agents Analyze Real-World Spatial Biology Data?},
  author = {Workman, Kenny and Yang, Zhen and Muralidharan, Harihara and Le, Hannah},
  year = {2025},
  url = {https://github.com/latchbio/spatialbench}
}
```
