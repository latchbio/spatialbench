# Adding Evaluations to SpatialBench

This guide walks you through adding a new evaluation to SpatialBench step by step.

## Quick Checklist

- [ ] Choose a task from real-world analysis workflows
- [ ] Establish reproducible ground truth
- [ ] Select appropriate grader(s)
- [ ] Write eval JSON with clear task description
- [ ] Test locally
- [ ] Document in evals/README.md
- [ ] Submit PR

## Detailed Walkthrough

### Step 1: Choose Your Task

Good evaluation tasks:
- Represent real analysis workflows
- Have clear, objective ground truth
- Test specific agent capabilities
- Vary in difficulty

Examples:
- **Easy**: Calculate mean gene count per cell
- **Medium**: Perform Leiden clustering with reasonable resolution
- **Hard**: Identify rare cell populations using multiple markers

### Step 2: Prepare Your Dataset

Ensure your dataset:
- Is in standard format (.h5ad for most cases)
- Has necessary metadata (cell types, clusters, spatial coords)
- Is properly preprocessed (or evaluation tests preprocessing)
- Is hosted in accessible cloud storage

Upload to Latch:
```bash
latch cp local_data.h5ad latch://account/path/to/data.h5ad
```

### Step 3: Establish Ground Truth

Run the analysis manually using standard tools:

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

See [graders.md](graders.md) for full documentation.

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

### Step 6: Write Eval JSON

Create your evaluation file:

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

### Step 8: Document

Add to `evals/README.md`:

```markdown
#### platform_task_description_v1

**Category**: QC/Preprocessing/Clustering/Cell Typing/DE/Spatial
**Platform**: Xenium/AtlasXomics/Vizgen/Seeker
**Grader**: grader_name
**Difficulty**: ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Hard

Description of what this eval tests and why it's important.

**Key Features**:
- Tests X capability
- Requires Y knowledge
- Validates Z

**Reference**: [Paper/Protocol if applicable]
```

### Step 9: Submit Pull Request

Use this PR template:

```markdown
## New Evaluation: [Eval ID]

**Category**: [QC/Preprocessing/etc.]
**Platform**: [Xenium/AtlasXomics/etc.]
**Difficulty**: [Easy/Medium/Hard]

### Description

Brief description of what this evaluation tests.

### Ground Truth

How was ground truth established?
- Tool: scanpy 1.9.1
- Method: Standard preprocessing pipeline
- Parameters: [list key parameters]
- Reference: [paper/protocol link if applicable]

### Testing

- [x] Eval passes with correct answer
- [x] Eval fails with incorrect answer
- [x] Task description is clear and unambiguous
- [x] Ground truth is reproducible

### Files Changed

- `evals/category/eval_id.json` - New evaluation
- `evals/README.md` - Documentation

### Additional Notes

[Any special notes, edge cases, or considerations]
```

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

## Examples to Learn From

Study these well-designed evals:

- **Simple numeric**: `evals/qc/xenium_qc_basic.json`
- **Label set**: `evals/cell_typing/xenium_kidney_typing.json`
- **Multi-field**: `evals/preprocessing/xenium_normalization.json`
- **Complex**: `evals/clustering/atlasxomics_leiden.json`

## Need Help?

- Check existing evals for examples
- Read [specification.md](specification.md) for format details
- Read [graders.md](graders.md) for grader options
- Open an issue for questions
- Ask in discussions for design feedback
