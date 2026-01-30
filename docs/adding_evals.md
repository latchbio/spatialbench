# Understanding SpatialBench Evaluations

This guide explains how SpatialBench evaluations are structured and how they work. The 7 example evaluations in this repository are fixed to demonstrate the format. To contribute to the full 98-evaluation benchmark, contact [kenny@latch.bio](mailto:kenny@latch.bio).

## Example Evaluation Structure

The 7 evaluations in this repository demonstrate:

- [ ] Tasks from real-world analysis workflows
- [ ] Reproducible ground truth
- [ ] Appropriate grader selection
- [ ] Clear task descriptions with specified output format
- [ ] Local testing procedures
- [ ] Comprehensive documentation

## Full Benchmark Information

The complete SpatialBench comprises **98 evaluations** across four platforms:

| Technology       | Evaluations |
|------------------|-------------|
| Xenium           | 30          |
| Vizgen (MERFISH) | 31          |
| AtlasXomics      | 25          |
| Seeker/Curio     | 12          |
| **Total**        | **98**      |

This repository contains **7 representative examples** to demonstrate the evaluation format and grading system. To contribute to the full benchmark, contact [kenny@latch.bio](mailto:kenny@latch.bio).

## Detailed Walkthrough

### Step 1: Task Selection

Good evaluation tasks in SpatialBench:
- Represent real analysis workflows
- Have clear, objective ground truth
- Test specific agent capabilities
- Span diverse difficulty levels

Examples from the benchmark:
- Calculate mean gene count per cell (QC metrics)
- Perform Leiden clustering with specific parameters
- Identify cell populations using marker genes

### Step 2: Dataset Requirements

SpatialBench datasets:
- Are in standard format (.h5ad for most cases)
- Have necessary metadata (cell types, clusters, spatial coords)
- Are properly preprocessed (or evaluations test preprocessing)
- Are hosted in cloud storage with latch:// URIs

Example data node:
```json
{
  "data_node": "latch://38438.account/xenium_kidney.h5ad"
}
```

### Step 3: Ground Truth Methodology

Ground truth is established by running analyses with standard tools:

```python
import scanpy as sc
import numpy as np

adata = sc.read_h5ad("dataset.h5ad")

sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)

sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000)

sc.pp.pca(adata, n_comps=50)

ground_truth = {
    "n_cells": int(adata.n_obs),
    "n_genes": int(adata.n_vars),
    "mean_counts": float(adata.X.sum(axis=1).mean()),
    "n_pcs": int(adata.obsm['X_pca'].shape[1])
}

print(ground_truth)
```

**Document everything**:
- Package versions (`scanpy==1.9.1`)
- Random seeds (if applicable)
- Parameter choices and rationale
- References to papers/protocols

### Step 4: Select Grader

Match your task to the appropriate grader:

| Output Type | Grader | Example |
|-------------|--------|---------|
| Numbers | NumericTolerance | `{"mean": 45.2}` |
| Label set | LabelSetJaccard | `{"labels": ["A", "B"]}` |
| Percentages | DistributionComparison | `{"dist": {"A": 30, "B": 70}}` |
| Ranked list | MarkerGenePrecisionRecall | `{"genes": ["G1", "G2"]}` |
| Expression scores | MarkerGeneSeparation | `{"auroc": 0.85, "per_gene": [...]}` |
| Spatial metrics | SpatialAdjacency | `{"median_dist": 18.5}` |

See [eval-graders](https://github.com/latchbio/eval-graders) for full documentation.

### Step 5: Write Task Description

Make it crystal clear:

**Bad**:
```
"Cluster the cells and tell me how many clusters there are."
```

**Good**:
```
"Perform Leiden clustering on the preprocessed data using resolution=1.0.
Ensure resulting clusters are largely independent of sample batch
(adjusted mutual information with 'sample' column < 0.3).
Return JSON with fields: num_clusters (int), cluster_labels (list of unique
cluster IDs), ami_with_sample (float between 0 and 1)."
```

Key elements:
- Specific method (Leiden, not just "clustering")
- Parameters (resolution=1.0)
- Constraints (AMI < 0.3)
- Exact output format with field names and types

### Step 6: Evaluation JSON Format

Example evaluation file structure:

```json
{
  "id": "platform_task_description_v1",
  "task": "Your detailed task description here...",
  "data_node": "latch://path/to/dataset.h5ad",
  "grader": {
    "type": "grader_name",
    "config": {
      "ground_truth": {
        ...
      },
      "tolerances": {
        ...
      }
    }
  }
}
```

**Naming convention**:
- `id`: `xenium_clustering_leiden_v1`
- File: `evals/clustering/xenium_clustering_leiden.json`

### Step 7: Test Locally

Create a test agent:

```python
from spatialbench import EvalRunner
from pathlib import Path
import json

def test_agent(task_prompt, work_dir):
    import scanpy as sc

    adata_files = list(work_dir.glob("*.h5ad"))
    adata = sc.read_h5ad(adata_files[0])

    sc.pp.pca(adata, n_comps=50)

    answer = {
        "n_pcs": adata.obsm['X_pca'].shape[1]
    }

    answer_file = work_dir / "eval_answer.json"
    answer_file.write_text(json.dumps(answer))

    return answer

runner = EvalRunner(
    "evals/preprocessing/my_new_eval.json",
    keep_workspace=True
)
result = runner.run(agent_function=test_agent)

print(f"Passed: {result['passed']}")
```

**Test both cases**:
1. Correct answer → should pass
2. Incorrect answer → should fail

```python
def wrong_agent(task_prompt, work_dir):
    answer = {"n_pcs": 999}
    (work_dir / "eval_answer.json").write_text(json.dumps(answer))
    return answer

result = runner.run(agent_function=wrong_agent)
assert not result['passed'], "Grader should fail with wrong answer!"
```

### Step 8: Documentation Format

Each evaluation in `evals/README.md` is documented with:

```markdown
#### platform_task_description

**Platform**: Xenium/Vizgen/Seeker
**Grader**: grader_name

Description of what this eval tests and why it's important.

**Key Metrics**: field1, field2, field3

**Platform Notes**: Specific considerations for this platform

**Challenges**: What makes this task difficult
```

### Step 9: Contributing to the Full Benchmark

To contribute new evaluations to the full 98-evaluation benchmark:

1. **Review the 7 examples** in this repository to understand format and quality standards
2. **Contact [kenny@latch.bio](mailto:kenny@latch.bio)** with your proposal
3. **Provide**:
   - Task description and rationale
   - Ground truth establishment method
   - Dataset information
   - Grader configuration
   - Validation of reproducibility

The full benchmark is maintained separately to prevent overfitting and ensure performance metrics reflect genuine spatial biology reasoning capabilities.

## Common Pitfalls

### ❌ Ambiguous Task Descriptions

**Problem**: Agent doesn't know exact output format
```json
{
  "task": "Find the major cell types"
}
```

**Solution**: Specify exact fields
```json
{
  "task": "Identify major cell types and return JSON with field: cell_types (list of strings)"
}
```

### ❌ Too Tight Tolerances

**Problem**: Ground truth not reproducible enough
```json
{
  "mean_expression": 45.234567,
  "tolerance": 0.00001
}
```

**Solution**: Use reasonable tolerances
```json
{
  "mean_expression": 45.2,
  "tolerance": 2.0
}
```

### ❌ Missing Validation

**Problem**: Don't test with wrong answers

**Solution**: Always test failure cases

### ❌ Underdocumented Ground Truth

**Problem**: Can't reproduce analysis

**Solution**: Document all parameters, seeds, versions

## Advanced: Multiple Graders

Some evals need multiple criteria:

```json
{
  "grader": {
    "type": "multi_criteria",
    "graders": [
      {
        "type": "numeric_tolerance",
        "weight": 0.5,
        "config": {...}
      },
      {
        "type": "label_set_jaccard",
        "weight": 0.5,
        "config": {...}
      }
    ]
  }
}
```

**Note**: This requires implementing a `MultiCriteriaGrader` - see custom grader docs.

## Tips for Good Evaluations

1. **Start simple**: Don't combine too many requirements in one eval
2. **Be specific**: Exact field names, data types, constraints
3. **Document well**: Future you will thank you
4. **Test thoroughly**: Both pass and fail cases
5. **Consider difficulty**: Mix easy, medium, and hard evals
6. **Real-world relevance**: Does this test actual analysis skills?
7. **Reproducibility**: Can someone else verify your ground truth?

## Example Evaluations to Study

The 7 representative evaluations in this repository:

- **QC metrics**: `evals/qc/seeker_qc_basic.json`
- **Preprocessing**: `evals/preprocessing/xenium_normalization.json`
- **Clustering**: `evals/clustering/xenium_leiden.json`
- **Cell typing**: `evals/cell_typing/xenium_kidney_typing.json`
- **Differential expression**: `evals/differential_expression/vizgen_de_temporal.json`
- **Spatial analysis**: `evals/spatial_analysis/seeker_spatial_contiguity.json`, `evals/spatial_analysis/vizgen_tissue_composition.json`

## Additional Resources

- Study the 7 example evaluations for format and structure
- Read [specification.md](specification.md) for technical format details
- See [eval-graders](https://github.com/latchbio/eval-graders) for available grader types
- See [BENCHMARK_SCOPE.md](../BENCHMARK_SCOPE.md) for full benchmark information
- Contact [kenny@latch.bio](mailto:kenny@latch.bio) to contribute to the full benchmark
