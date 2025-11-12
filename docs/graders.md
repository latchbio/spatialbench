# Grader API Documentation

SpatialBench includes 6 built-in graders for evaluating different types of analysis outputs. This document provides comprehensive documentation for each grader.

## Table of Contents

1. [Base Grader API](#base-grader-api)
2. [NumericToleranceGrader](#numerictolerancegrader)
3. [LabelSetJaccardGrader](#labelsetjaccardgrader)
4. [DistributionComparisonGrader](#distributioncomparisongrader)
5. [MarkerGenePrecisionRecallGrader](#markergeneprecisionrecallgrader)
6. [MarkerGeneSeparationGrader](#markergeneseparationgrader)
7. [SpatialAdjacencyGrader](#spatialadjacencygrader)
8. [Creating Custom Graders](#creating-custom-graders)

## Base Grader API

All graders inherit from `BinaryGrader`:

```python
from spatialbench.graders.base import BinaryGrader, GraderResult

class BinaryGrader:
    def evaluate(self, test_result: TestResult, config: dict) -> GraderResult:
        """Extract answer and evaluate."""

    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        """Core grading logic - override this."""

    def extract_answer_from_tags(self, conversation: list[dict]) -> dict | None:
        """Extract answer from agent conversation."""
```

**GraderResult**:
```python
@dataclass
class GraderResult:
    passed: bool              # Did the evaluation pass?
    metrics: dict             # Detailed metrics
    reasoning: str            # Human-readable explanation
    agent_answer: dict | None  # The agent's answer
```

---

## NumericToleranceGrader

Validates numeric fields against ground truth with configurable tolerances.

### Use Cases

- QC metrics (gene counts, UMI counts, mito fraction)
- Statistical summaries (mean, median, std)
- Dimensionality parameters (number of PCs)
- Any numeric comparison

### Config Schema

```python
{
    "ground_truth": {
        "field_name": numeric_value,
        ...
    },
    "tolerances": {
        "field_name": {
            "type": "absolute" | "relative" | "min" | "max",
            "value": numeric_tolerance
        },
        ...
    }
}
```

### Tolerance Types

**Absolute**: `|actual - expected| <= tolerance`
```json
{
    "type": "absolute",
    "value": 5.0
}
```

**Relative**: `|actual - expected| / |expected| <= tolerance`
```json
{
    "type": "relative",
    "value": 0.1
}
```

**Min**: `actual >= expected` (minimum threshold)
```json
{
    "type": "min",
    "value": 100
}
```

**Max**: `actual <= expected` (maximum threshold)
```json
{
    "type": "max",
    "value": 0.35
}
```

### Example

```json
{
    "type": "numeric_tolerance",
    "config": {
        "ground_truth": {
            "mean_genes": 44.6,
            "median_genes": 44.0,
            "p95_mito_frac": 0.30
        },
        "tolerances": {
            "mean_genes": {"type": "absolute", "value": 5.0},
            "median_genes": {"type": "absolute", "value": 5.0},
            "p95_mito_frac": {"type": "max", "value": 0.35}
        }
    }
}
```

**Expected agent output**:
```json
{
    "mean_genes": 46.2,
    "median_genes": 43.5,
    "p95_mito_frac": 0.28
}
```

### Metrics

- `{field}_actual`: Agent's value
- `{field}_expected`: Ground truth value
- `{field}_error`: Absolute or relative error
- `{field}_pass`: Boolean pass/fail for this field

---

## LabelSetJaccardGrader

Compares sets of labels using Jaccard index.

### Use Cases

- Cell type vocabularies
- Cluster label sets
- Gene marker lists (when order doesn't matter)
- Any set comparison

### Config Schema

```python
{
    "ground_truth_labels": ["label1", "label2", ...],
    "scoring": {
        "method": "jaccard_index",
        "pass_threshold": 0.0 to 1.0
    }
}
```

### Jaccard Index

```
J(A, B) = |A ∩ B| / |A ∪ B|
```

- 1.0 = perfect match
- 0.0 = no overlap

### Example

```json
{
    "type": "label_set_jaccard",
    "config": {
        "ground_truth_labels": [
            "Pod", "Glom-EC", "EC", "PTS1", "PTS2",
            "PTS3", "DTL", "TAL", "DCT", "CNT"
        ],
        "scoring": {
            "method": "jaccard_index",
            "pass_threshold": 1.0
        }
    }
}
```

**Expected agent output**:
```json
{
    "cell_types_predicted": [
        "Pod", "Glom-EC", "EC", "PTS1", "PTS2",
        "PTS3", "DTL", "TAL", "DCT", "CNT"
    ]
}
```

### Metrics

- `jaccard_index`: Jaccard similarity score
- `true_positives`: Correct labels
- `false_positives`: Extra labels (not in ground truth)
- `false_negatives`: Missing labels (in ground truth, not predicted)
- `predicted_count`: Number of predicted labels
- `ground_truth_count`: Number of ground truth labels

---

## DistributionComparisonGrader

Validates cell type distributions (percentages).

### Use Cases

- Cell type composition
- Tissue proportions
- Cluster size validation
- Any percentage distribution

### Config Schema

```python
{
    "ground_truth": {
        "total_cells": int (optional),
        "cell_type_distribution": {
            "type1": percentage1,
            "type2": percentage2,
            ...
        }
    },
    "tolerances": {
        "total_cells": {"type": "absolute", "value": int},
        "cell_type_percentages": {"value": float}
    }
}
```

### Example

```json
{
    "type": "distribution_comparison",
    "config": {
        "ground_truth": {
            "total_cells": 50000,
            "cell_type_distribution": {
                "Neuron": 45.2,
                "Astrocyte": 20.1,
                "Oligodendrocyte": 15.3,
                "Microglia": 10.2,
                "Endothelial": 9.2
            }
        },
        "tolerances": {
            "total_cells": {"type": "absolute", "value": 1000},
            "cell_type_percentages": {"value": 3.0}
        }
    }
}
```

**Expected agent output**:
```json
{
    "total_cells": 49800,
    "cell_type_distribution": {
        "Neuron": 44.8,
        "Astrocyte": 21.0,
        "Oligodendrocyte": 14.9,
        "Microglia": 10.5,
        "Endothelial": 8.8
    }
}
```

### Metrics

- `total_cells_actual`, `total_cells_expected`, `total_cells_pass`
- For each cell type:
  - `{type}_actual`: Agent's percentage
  - `{type}_expected`: Ground truth percentage
  - `{type}_diff`: Absolute difference
  - `{type}_pass`: Within tolerance?
- `extra_cell_types`: Cell types not in ground truth

---

## MarkerGenePrecisionRecallGrader

Evaluates top-K marker gene lists using Precision@K and Recall@K.

### Use Cases

- Marker gene discovery
- Differential expression top genes
- Ranked gene lists
- Feature selection validation

### Config Schema

```python
{
    "canonical_markers": ["gene1", "gene2", ...],
    "scoring": {
        "pass_thresholds": {
            "precision_at_k": 0.0 to 1.0,
            "recall_at_k": 0.0 to 1.0
        }
    }
}
```

### Metrics

**Precision@K**: Fraction of predicted genes that are canonical
```
P@K = |predicted ∩ canonical| / K
```

**Recall@K**: Fraction of canonical genes found in top-K
```
R@K = |predicted ∩ canonical| / |canonical|
```

### Example

```json
{
    "type": "marker_gene_precision_recall",
    "config": {
        "canonical_markers": [
            "NPHS1", "NPHS2", "PODXL", "WT1",
            "SYNPO", "MAGI2", "CD2AP", "ACTN4"
        ],
        "scoring": {
            "pass_thresholds": {
                "precision_at_k": 0.60,
                "recall_at_k": 0.50
            }
        }
    }
}
```

**Expected agent output**:
```json
{
    "top_marker_genes": [
        "NPHS1", "NPHS2", "PODXL", "WT1", "SYNPO",
        "CDH5", "PECAM1", "VWF"
    ]
}
```

K = 8 (length of predicted list)
- Precision@8 = 5/8 = 0.625 ✓ (≥0.60)
- Recall@8 = 5/8 = 0.625 ✓ (≥0.50)

### Metrics

- `k`: Length of predicted list
- `precision_at_k`: Precision score
- `recall_at_k`: Recall score
- `true_positives`: Correct genes
- `false_positives`: Non-canonical genes
- `false_negatives`: Canonical genes not found
- `precision_pass`, `recall_pass`: Individual pass/fail

**Note**: Gene name matching is case-insensitive.

---

## MarkerGeneSeparationGrader

Validates marker expression separation using AUROC (Area Under ROC Curve).

### Use Cases

- Validate markers actually separate cell types
- Expression-based cell type validation
- Marker quality assessment

### Config Schema

```python
{
    "scoring": {
        "pass_thresholds": {
            "mean_auroc": 0.0 to 1.0,
            "fraction_high": 0.0 to 1.0,
            "per_gene_cutoff": 0.0 to 1.0
        }
    }
}
```

### Metrics

**Mean AUROC**: Average AUROC across all markers
**Fraction High**: Fraction of markers with AUROC ≥ cutoff

AUROC interpretation:
- 1.0 = perfect separation
- 0.5 = random (no separation)
- Close to 1.0 = good marker

### Example

```json
{
    "type": "marker_gene_separation",
    "config": {
        "scoring": {
            "pass_thresholds": {
                "mean_auroc": 0.85,
                "fraction_high": 0.70,
                "per_gene_cutoff": 0.80
            }
        }
    }
}
```

**Expected agent output**:
```json
{
    "mean_auroc": 0.87,
    "per_gene_stats": [
        {"gene": "NPHS1", "auroc": 0.92},
        {"gene": "NPHS2", "auroc": 0.89},
        {"gene": "PODXL", "auroc": 0.85},
        {"gene": "WT1", "auroc": 0.88},
        {"gene": "SYNPO", "auroc": 0.75}
    ]
}
```

- Mean AUROC: 0.87 ✓ (≥0.85)
- Fraction high (≥0.80): 4/5 = 0.80 ✓ (≥0.70)

### Metrics

- `mean_auroc_agent`: Agent's reported mean
- `mean_auroc_computed`: Computed from per_gene_stats
- `fraction_high`: Fraction above cutoff
- `high_auroc_genes`: Genes ≥ cutoff
- `low_auroc_genes`: Genes < cutoff
- `per_gene_aurocs`: Full dict of gene → AUROC

---

## SpatialAdjacencyGrader

Evaluates spatial proximity metrics (cell-cell distances).

### Use Cases

- Spatial adjacency analysis
- Cell-cell interaction validation
- Spatial organization metrics

### Config Schema

```python
{
    "scoring": {
        "pass_thresholds": {
            "max_median_ic_to_pc_um": float,
            "max_p90_ic_to_pc_um": float,
            "min_pct_ic_within_15um": float,
            "min_pct_ic_mixed_within_55um": float
        }
    }
}
```

### Example

```json
{
    "type": "spatial_adjacency",
    "config": {
        "scoring": {
            "pass_thresholds": {
                "max_median_ic_to_pc_um": 25.0,
                "max_p90_ic_to_pc_um": 80.0,
                "min_pct_ic_within_15um": 60.0,
                "min_pct_ic_mixed_within_55um": 60.0
            }
        }
    }
}
```

**Expected agent output**:
```json
{
    "median_ic_to_pc_um": 18.5,
    "p90_ic_to_pc_um": 65.2,
    "pct_ic_within_15um": 72.3,
    "pct_ic_mixed_within_55um": 85.1,
    "adjacency_pass": true
}
```

### Metrics

- `median_ic_to_pc_um`: Median distance IC→PC
- `p90_ic_to_pc_um`: 90th percentile distance
- `pct_ic_within_15um`: % IC cells within 15μm of PC
- `pct_ic_mixed_within_55um`: % IC cells with PC neighbor within 55μm
- `adjacency_pass`: Agent's assessment
- Individual pass/fail for each metric

---

## Creating Custom Graders

See [CONTRIBUTING.md](../CONTRIBUTING.md#creating-a-custom-grader) for a complete guide.

### Basic Template

```python
from spatialbench.graders.base import BinaryGrader, GraderResult

class MyGrader(BinaryGrader):
    def evaluate_answer(self, agent_answer: dict, config: dict) -> GraderResult:
        passed = True
        metrics = {}
        failures = []

        reasoning = f"My Grader: {'PASS' if passed else 'FAIL'}"

        return GraderResult(
            passed=passed,
            metrics=metrics,
            reasoning=reasoning,
            agent_answer=agent_answer
        )
```

### Register Your Grader

Add to `spatialbench/graders/__init__.py`:

```python
from spatialbench.graders.my_grader import MyGrader

GRADER_REGISTRY = {
    ...
    "my_grader": MyGrader,
}
```

### Use in Evaluation

```json
{
    "grader": {
        "type": "my_grader",
        "config": {...}
    }
}
```

## Grader Selection Guide

| Task Type | Recommended Grader | Notes |
|-----------|-------------------|-------|
| QC metrics | NumericTolerance | Use absolute tolerances |
| Cell type vocab | LabelSetJaccard | Set threshold=1.0 for exact match |
| Tissue composition | DistributionComparison | ±3% typical tolerance |
| Top-K markers | MarkerGenePrecisionRecall | Balance P@K and R@K |
| Marker validation | MarkerGeneSeparation | Require AUROC >0.8 |
| Spatial metrics | SpatialAdjacency | Platform-specific thresholds |
| Clustering | NumericTolerance + LabelSetJaccard | Multiple metrics |
| Custom logic | Create custom grader | Full control |
