# SpatialBench

**A benchmark for evaluating AI agents on spatial biology analysis tasks**

SpatialBench is a comprehensive evaluation framework designed to test the capabilities of Large Language Models (LLMs) and AI agents on real-world spatial transcriptomics and epigenomics analysis workflows. The benchmark includes evaluations across multiple platforms (Xenium, AtlasXomics ATAC-seq, Vizgen MERFISH, Curio Seeker) and covers key analysis tasks from quality control to differential expression.

## Overview

SpatialBench provides:
- **Standardized evaluation format**: JSON-based test cases with clear task specifications
- **Extensible grading system**: Multiple grader types for different evaluation criteria
- **Platform coverage**: Evals for RNA (Xenium, MERFISH, Seeker) and ATAC-seq (AtlasXomics)
- **Task diversity**: QC, preprocessing, clustering, cell typing, differential expression, and spatial analysis
- **Framework-agnostic**: Works with any agent that can write JSON outputs

## Quick Start

### Installation

```bash
pip install spatialbench
```

### Running an Evaluation

```python
from spatialbench import EvalRunner

def my_agent(task_prompt, work_dir):
    import json
    answer = {"num_clusters": 6}
    answer_file = work_dir / "eval_answer.json"
    answer_file.write_text(json.dumps(answer))
    return answer

runner = EvalRunner("evals/clustering/atlasxomics_leiden.json")
result = runner.run(agent_function=my_agent)

print(f"Passed: {result['passed']}")
```

## Evaluation Categories

### Quality Control (QC)
Assess basic dataset properties: gene counts, UMI counts, mitochondrial fraction, etc.

**Example**: `evals/qc/xenium_qc_basic.json`

### Preprocessing
Test normalization, dimensionality reduction, and batch correction pipelines.

**Example**: `evals/preprocessing/xenium_normalization.json`

### Clustering
Evaluate clustering algorithm application and parameter selection.

**Example**: `evals/clustering/atlasxomics_leiden.json`

### Cell Type Annotation
Test marker-based cell type assignment and biological reasoning.

**Example**: `evals/cell_typing/xenium_kidney_typing.json`

### Differential Expression
Assess statistical testing and marker gene discovery.

**Example**: `evals/differential_expression/atlasxomics_de_markers.json`

### Spatial Analysis
Evaluate spatial-specific analyses like tissue composition and cell-cell interactions.

**Example**: `evals/spatial_analysis/vizgen_tissue_composition.json`

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

## Documentation

- [Evaluation Specification](docs/specification.md)
- [Grader API](docs/graders.md)
- [Adding Evaluations](docs/adding_evals.md)
- [Evaluation Catalog](evals/README.md)

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
