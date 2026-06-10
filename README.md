# SpatialBench

**Can AI agents extract biological insight from real-world spatial data?**

SpatialBench is a benchmark of 159 verifiable problems derived from practical spatial transcriptomics workflows. Each problem snapshots an analysis state immediately before a target step and pairs it with a deterministic grader that evaluates recovery of a key biological result.

This revised version of the benchmark includes 159 problems across 5 platforms and 7 task categories.  We share results for the full benchmark and publicly release a representative sample covering all platform types and task categories along with the associated agent trajectories. We withhold releasing the full benchmark set publicly to avoid contamination.


## Key Findings
| model_name                    | harness        |   Accuracy (%) |   Cost ($) |
|:------------------------------|:---------------|---------------:|-----------:|
| gpt-5.5                       | mini-swe-agent |          57.65 |     1.1207 |
| gpt-5.4                       | mini-swe-agent |          57.44 |     0.577  |
| gemini-3.5-flash              | pi             |          55.56 |     1.4254 |
| claude-opus-4-8               | claude-code    |          55.35 |     0.8776 |
| gpt-5.5                       | openai-codex   |          53.67 |     3.1616 |
| claude-opus-4-6               | mini-swe-agent |          52.83 |     0.8456 |
| claude-opus-4-8               | mini-swe-agent |          52.62 |     1.1061 |
| claude-opus-4-7               | mini-swe-agent |          52.41 |     0.9817 |
| gemini-3.1-pro-preview        | mini-swe-agent |          51.57 |     0.9362 |
| claude-opus-4-7               | claude-code    |          51.36 |     0.8023 |
| gpt-5.2                       | mini-swe-agent |          50.1  |     0.6024 |
| gemini-3.5-flash              | mini-swe-agent |          48.85 |     2.7608 |
| grok-4.20-beta-0309-reasoning | mini-swe-agent |          45.91 |     0.1679 |
| claude-sonnet-4-6             | mini-swe-agent |          44.23 |     0.273  |
| claude-opus-4-5               | mini-swe-agent |          42.77 |     0.4624 |
| claude-sonnet-4-5             | mini-swe-agent |          41.51 |     0.2247 |
| gpt-5.1                       | mini-swe-agent |          39.83 |     0.1574 |
| grok-4-1-fast-reasoning       | mini-swe-agent |          33.96 |     0.0164 |
| grok-4                        | mini-swe-agent |          31.87 |     0.4529 |
| gemini-2.5-pro                | mini-swe-agent |          28.93 |     0.1086 |

Full results with 95% confidence intervals are in [`results/`](results/). Details on implementation methodology can be found in [Methods](METHODS.md)


## Benchmark Structure

**159 evaluations** across:
- **5 platforms**: Curio,Vizgen,Xenium,AtlasXOmics,Visium
- **7 task categories**: Dimensionality Reduction,Cell Typing,Normalization,Differential Expression,Clustering,QC,Spatial Analysis

Tasks require empirical interaction with the data—agents that rely on prior knowledge without performing the requisite analysis fail to complete many tasks correctly.

## Quick Start

```bash
pip install -e .

# Validate evaluation format
spatialbench validate evals/xenium/xenium_kidney_spatial_cn7_composition_day14.json

# Run with mini-swe-agent
export ANTHROPIC_API_KEY=your_key
spatialbench run evals/xenium/xenium_kidney_spatial_cn7_composition_day14.json --agent minisweagent --model anthropic/claude-opus-4-5

export OPENAI_API_KEY=your_key
spatialbench run evals/xenium/xenium_kidney_spatial_cn7_composition_day14.json --agent minisweagent --model openai/gpt-5.5
```

## Graders

Five grader families handle different answer types:

| Grader | Use Case |
|--------|----------|
| NumericTolerance | QC metrics, counts, expression values |
| MultipleChoice | Discrete interpretation questions |
| MarkerGenePrecisionRecall | Gene lists (P@K, R@K) |
| LabelSetJaccard | Cell type sets |
| DistributionComparison | Cell type proportions |

See [latch-eval-tools](https://github.com/latchbio/latch-eval-tools) for implementations and harness setups. 

## Citation

```bibtex
@article{spatialbench2025,
  title = {SpatialBench: Can Agents Analyze Real-World Spatial Biology Data?},
  author = {Workman, Kenny and Yang, Zhen and Muralidharan, Harihara and Le, Hannah},
  year = {2025},
  url = {https://github.com/latchbio/spatialbench}
}
```

## License

Apache 2.0
