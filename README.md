# SpatialBench

**A benchmark for evaluating AI agents on spatial biology analysis tasks**

SpatialBench is a comprehensive evaluation framework designed to test the capabilities of Large Language Models (LLMs) and AI agents on real-world spatial transcriptomics and epigenomics analysis workflows. The full benchmark comprises **98 evaluations** across multiple platforms (Xenium, Vizgen MERFISH, AtlasXomics ATAC-seq, Curio Seeker) and covers key analysis tasks from quality control to differential expression.

**This repository contains 7 representative examples** from the full benchmark to demonstrate the evaluation format and grading system. The complete benchmark is withheld to prevent overfitting and ensure reliable model comparisons.

## Overview

### Full Benchmark Scale

| Technology       | Evaluations |
|------------------|-------------|
| Xenium           | 30          |
| Vizgen (MERFISH) | 31          |
| AtlasXomics      | 25          |
| Seeker/Curio     | 12          |
| **Total**        | **98**      |

### This Repository

This repository contains **7 example evaluations** that demonstrate:
- **Standardized evaluation format**: JSON-based test cases with clear task specifications
- **Extensible grading system**: Multiple grader types for different evaluation criteria
- **Platform coverage**: Examples from RNA (Xenium, MERFISH, Seeker) and ATAC-seq platforms
- **Task diversity**: Samples across QC, preprocessing, clustering, cell typing, differential expression, and spatial analysis
- **Framework-agnostic**: Works with any agent that can write JSON outputs

The full 98-evaluation benchmark is withheld to prevent overfitting and ensure that performance metrics reflect genuine spatial biology reasoning capabilities rather than memorization.

## Quick Start

### Installation

```bash
pip install spatialbench
```

### Running an Evaluation

**Using mini-swe-agent (Recommended)**

SpatialBench includes built-in support for [mini-swe-agent](https://github.com/anthropics/mini-swe-agent):

```bash
# Install spatialbench with mini-swe-agent
pip install spatialbench

# Configure your model
export MSWEA_MODEL_NAME=anthropic/claude-sonnet-4-5
export ANTHROPIC_API_KEY=your_api_key

# Run a single evaluation
spatialbench run evals/qc/seeker_qc_basic.json --agent minisweagent

# Run batch evaluations
spatialbench batch evals_full/seeker \
  --agent minisweagent \
  --model anthropic/claude-sonnet-4-5 \
  --output results/run1 \
  --parallel 6 \
  --keep-workspace
```

Or programmatically:

```python
from spatialbench import EvalRunner, run_minisweagent_task

runner = EvalRunner("evals/qc/seeker_qc_basic.json")
result = runner.run(agent_function=run_minisweagent_task)

print(f"Passed: {result['passed']}")
```

**Using a custom agent**

```python
from spatialbench import EvalRunner

def my_agent(task_prompt, work_dir):
    import json
    answer = {"mean_genes_per_bead": 45.2}
    answer_file = work_dir / "eval_answer.json"
    answer_file.write_text(json.dumps(answer))
    return answer

runner = EvalRunner("evals/qc/seeker_qc_basic.json")
result = runner.run(agent_function=my_agent)

print(f"Passed: {result['passed']}")
```

## Task Categories

The full benchmark spans six major categories of spatial biology analysis. This repository includes one representative example from each:

### Quality Control (QC)
Assess basic dataset properties: gene counts, UMI counts, mitochondrial fraction, etc.

**Example**: `evals/qc/seeker_qc_basic.json`

### Preprocessing
Test normalization, dimensionality reduction, and batch correction pipelines.

**Example**: `evals/preprocessing/xenium_normalization.json`

### Clustering
Evaluate clustering algorithm application and parameter selection.

**Example**: `evals/clustering/xenium_leiden.json`

### Cell Type Annotation
Test marker-based cell type assignment and biological reasoning.

**Example**: `evals/cell_typing/xenium_kidney_typing.json`

### Differential Expression
Assess statistical testing and marker gene discovery.

**Example**: `evals/differential_expression/vizgen_de_temporal.json`

### Spatial Analysis
Evaluate spatial-specific analyses like tissue composition and spatial contiguity.

**Examples**: `evals/spatial_analysis/seeker_spatial_contiguity.json`, `evals/spatial_analysis/vizgen_tissue_composition.json`

## Grader System

SpatialBench includes 6 built-in graders:

1. **NumericToleranceGrader**: For QC metrics, counts, percentages
2. **LabelSetJaccardGrader**: For cell type label sets
3. **DistributionComparisonGrader**: For cell type proportions
4. **MarkerGenePrecisionRecallGrader**: For marker gene lists (P@K, R@K)
5. **MarkerGeneSeparationGrader**: For expression-based validation (AUROC)
6. **SpatialAdjacencyGrader**: For spatial proximity metrics

See [docs/graders.md](docs/graders.md) for detailed documentation.

## Evaluation Format

Evaluations are defined in JSON:

```json
{
  "id": "eval_identifier",
  "task": "Natural language task description...",
  "data_node": "latch://path/to/dataset.h5ad",
  "grader": {
    "type": "numeric_tolerance",
    "config": {
      "ground_truth": {"field": 100},
      "tolerances": {"field": {"type": "absolute", "value": 5}}
    }
  }
}
```

See [docs/specification.md](docs/specification.md) for the complete specification.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding new evaluations
- Creating custom graders
- Submitting benchmark results

## Batch Evaluations

SpatialBench supports batch evaluation with parallel execution:

```bash
spatialbench batch evals_full/seeker \
  --agent minisweagent \
  --model anthropic/claude-sonnet-4-5 \
  --output results/run1 \
  --parallel 6 \
  --keep-workspace
```

For running benchmarks across multiple models, use the benchmark script:

```bash
./scripts/benchmark_models.sh evals_full/seeker 6 true
```

Results are organized by run timestamp in `results/run_TIMESTAMP/` directories.

For monitoring batch runs and troubleshooting, see [BATCH_MONITORING.md](BATCH_MONITORING.md).

### Batch Results

Batch runs produce:
- `batch_results.json` - Full results with pass/fail status, agent answers, and grader outputs
- `batch_log.txt` - Execution log with progress updates
- Agent metrics: cost, steps, duration per evaluation
- Summary statistics: pass rate, average cost, average steps

## Documentation

- [CLI Usage Guide](docs/CLI_USAGE.md)
- [Evaluation Specification](docs/specification.md)
- [Grader API](docs/graders.md)
- [Adding Evaluations](docs/adding_evals.md)
- [Evaluation Catalog](evals/README.md)
- [Batch Monitoring Guide](BATCH_MONITORING.md)

## Citation

If you use SpatialBench in your research, please cite:

```bibtex
@software{spatialbench2024,
  title = {SpatialBench: A Benchmark for AI Agents on Spatial Biology Analysis},
  author = {Latch Bio},
  year = {2024},
  url = {https://github.com/latchbio/spatialbench}
}
```

## License

Apache 2.0 - see [LICENSE](LICENSE) for details.
