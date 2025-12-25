# SpatialBench

**Can AI agents extract biological insight from real-world spatial data?**

SpatialBench is a benchmark of 146 verifiable problems derived from practical spatial transcriptomics workflows. Each problem snapshots an analysis state immediately before a target step and pairs it with a deterministic grader that evaluates recovery of a key biological result.

Across frontier models, accuracy remains low (20–38%), with strong model–task and model–platform interactions. Harness design (tools, prompts, control flow) affects outcomes as much as base model choice.

## Key Findings

| Model | Accuracy | Cost/Eval | Latency |
|-------|----------|-----------|---------|
| Opus-4.5 | 38.4% | $0.14 | 124s |
| GPT-5.2 | 34.0% | $0.04 | 89s |
| Sonnet-4.5 | 28.3% | $0.08 | 116s |
| GPT-5.1 | 27.4% | $0.02 | 56s |
| Grok-4.1 | 24.7% | $0.08 | 196s |
| Gemini-2.5-Pro | 20.1% | $0.19 | 194s |

Full results with 95% confidence intervals are in [`results/`](results/).

## Benchmark Structure

**146 evaluations** across:
- **5 platforms**: Xenium, Visium, MERFISH, Seeker, AtlasXomics
- **7 task categories**: QC, Normalization, Dimensionality Reduction, Clustering, Cell Typing, Differential Expression, Spatial Analysis

Tasks require empirical interaction with the data—agents that rely on prior knowledge without performing the requisite analysis fail to complete many tasks correctly.

## Canonical Examples

This repository includes 10 canonical examples in [`evals_canonical/`](evals_canonical/) demonstrating the evaluation format. The full benchmark is withheld to prevent overfitting.

| Task | Platform | Grader |
|------|----------|--------|
| QC | Xenium | Numeric |
| Normalization | MERFISH | Numeric |
| Dimensionality Reduction | Seeker | MCQ |
| Clustering | Visium | P@K |
| Clustering | MERFISH | MCQ |
| Cell Typing | Xenium | Cosine |
| Cell Typing | MERFISH | P@K |
| Differential Expression | Seeker | P@K |
| Spatial Analysis | Visium | Jaccard |
| Spatial Analysis | Xenium | MCQ |

## Quick Start

```bash
pip install -e .

# Validate an evaluation
spatialbench validate evals_canonical/qc/xenium_xenium_qc_filter_min_umi_counts.json

# Run with mini-swe-agent
export ANTHROPIC_API_KEY=your_key
spatialbench run evals_canonical/qc/xenium_xenium_qc_filter_min_umi_counts.json --agent minisweagent
```

### Custom Agent

```python
from spatialbench import EvalRunner

def my_agent(task_prompt, work_dir):
    import json
    answer = {"cells_after_filtering": 1374915}
    (work_dir / "eval_answer.json").write_text(json.dumps(answer))
    return answer

runner = EvalRunner("evals_canonical/qc/xenium_xenium_qc_filter_min_umi_counts.json")
result = runner.run(agent_function=my_agent)
print(f"Passed: {result['passed']}")
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

See [`spatialbench/graders/`](spatialbench/graders/) for implementations.

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
