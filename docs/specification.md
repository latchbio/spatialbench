# Evaluation Specification

This document defines the standard format for SpatialBench evaluations.

## JSON Schema

Every evaluation is defined as a JSON file with the following structure:

```json
{
  "id": "string",
  "task": "string",
  "data_node": "string | array<string> | null",
  "grader": {
    "type": "string",
    "config": {}
  },
  "timeout": "number (optional)",
  "download_timeout": "number (optional)",
  "agent_timeout": "number (optional)"
}
```

## Field Descriptions

### `id` (required)

Unique identifier for the evaluation.

**Format**: `platform_task_description_version`

**Examples**:
- `xenium_qc_basic`
- `atlasxomics_clustering_coarse_v1`
- `vizgen_cell_typing_astrocyte_v2`

**Best Practices**:
- Use lowercase with underscores
- Include platform name
- Add version suffix for iterations (`_v1`, `_v2`)
- Keep concise but descriptive

### `task` (required)

Natural language description of the analysis task.

**Guidelines**:
- Be specific and unambiguous
- Specify expected output format
- Include exact field names for JSON output
- Provide necessary biological context
- Mention any specific parameters or methods

**Example**:

```json
{
  "task": "Perform Leiden clustering on this AtlasXomics ATAC-seq dataset. Use resolution=1.0 and ensure clusters are independent of sample batch (AMI with sample < 0.3). Return JSON with fields: num_clusters (int), cluster_labels (list of unique cluster names), ami_with_sample (float)."
}
```

### `data_node` (optional)

Path(s) to dataset file(s) in cloud storage.

**Single file**:
```json
{
  "data_node": "latch://38438.account/path/to/dataset.h5ad"
}
```

**Multiple files**:
```json
{
  "data_node": [
    "latch://38438.account/path/to/file1.h5ad",
    "latch://38438.account/path/to/file2.csv"
  ]
}
```

**No data** (for synthetic or embedded data):
```json
{
  "data_node": null
}
```

**Supported formats**:
- `.h5ad` (AnnData - most common)
- `.csv` (tabular data)
- `.tsv` (tabular data)
- `.bed` (genomic regions)
- `.gz` (compressed files)

### `grader` (required)

Grading configuration specifying how to evaluate the agent's answer.

**Structure**:
```json
{
  "grader": {
    "type": "grader_name",
    "config": {
      "ground_truth": {},
      "tolerances": {},
      "scoring": {}
    }
  }
}
```

See [graders.md](graders.md) for detailed grader documentation.

### Timeout Fields (optional)

Control execution time limits:

- **`timeout`**: Overall evaluation timeout in seconds (default: 1200)
- **`download_timeout`**: Data download timeout in seconds (default: 600)
- **`agent_timeout`**: Agent execution timeout in seconds (default: 1200)

**Example**:
```json
{
  "timeout": 1800,
  "download_timeout": 300,
  "agent_timeout": 1500
}
```

## Output Format

Agents must write their answer as JSON to `eval_answer.json`:

```json
{
  "field1": value1,
  "field2": value2,
  ...
}
```

The fields must match those specified in the task description and expected by the grader.

## Complete Examples

### Numeric Tolerance (QC)

```json
{
  "id": "xenium_qc_basic",
  "task": "Calculate basic QC metrics for this Xenium dataset. Return JSON with fields: mean_genes_per_cell (float), median_genes_per_cell (float), std_genes_per_cell (float).",
  "data_node": "latch://38438.account/xenium_kidney.h5ad",
  "grader": {
    "type": "numeric_tolerance",
    "config": {
      "ground_truth": {
        "mean_genes_per_cell": 44.6,
        "median_genes_per_cell": 44.0,
        "std_genes_per_cell": 15.0
      },
      "tolerances": {
        "mean_genes_per_cell": {"type": "absolute", "value": 5.0},
        "median_genes_per_cell": {"type": "absolute", "value": 5.0},
        "std_genes_per_cell": {"type": "absolute", "value": 5.0}
      }
    }
  }
}
```

### Label Set (Cell Typing)

```json
{
  "id": "xenium_kidney_typing",
  "task": "Assign each cell to one of these 20 kidney cell types: Pod, Glom-EC, EC, PTS1, PTS2, PTS3, Inj_PT, FR_PT, DTL, TAL, DCT, CNT, PC, ICA, ICB, Uro, PEC, Fib, Per-SMC, Immune. Return JSON with field: cell_types_predicted (list of unique cell types found).",
  "data_node": "latch://38438.account/xenium_kidney.h5ad",
  "grader": {
    "type": "label_set_jaccard",
    "config": {
      "ground_truth_labels": [
        "Pod", "Glom-EC", "EC", "PTS1", "PTS2", "PTS3",
        "Inj_PT", "FR_PT", "DTL", "TAL", "DCT", "CNT",
        "PC", "ICA", "ICB", "Uro", "PEC", "Fib",
        "Per-SMC", "Immune"
      ],
      "scoring": {
        "method": "jaccard_index",
        "pass_threshold": 1.0
      }
    }
  }
}
```

### Distribution (Tissue Composition)

```json
{
  "id": "vizgen_tissue_composition",
  "task": "Calculate the percentage of each cell type in the tissue. Return JSON with fields: total_cells (int), cell_type_distribution (dict mapping cell_type to percentage).",
  "data_node": "latch://38438.account/vizgen_brain.h5ad",
  "grader": {
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
}
```

## Versioning

When updating an existing evaluation:

1. **Minor changes** (typo fixes, clarifications): Update in place
2. **Ground truth changes**: Create new version with `_v2` suffix
3. **Grader changes**: Create new version
4. **Task changes**: Create new version

Keep old versions for reproducibility.

## Validation

Before submitting, validate your evaluation:

```bash
spatialbench validate path/to/eval.json
```

This checks:
- JSON syntax
- Required fields present
- Grader type exists
- Config matches grader schema
- Data node paths are valid URIs

## Spatial Biology Conventions

### AnnData Structure

Standard fields in `.h5ad` files:

- `adata.X`: Expression matrix (cells × genes)
- `adata.obs`: Cell metadata (cell type, sample, QC metrics)
- `adata.var`: Gene metadata (gene names, chromosome)
- `adata.obsm['spatial']`: Spatial coordinates (x, y)
- `adata.uns`: Unstructured metadata

### Common Output Formats

**Cell types**: Use `adata.obs['cell_type']` or similar column

**Clusters**: Use `adata.obs['leiden']`, `adata.obs['louvain']`

**Embeddings**: Use `adata.obsm['X_pca']`, `adata.obsm['X_umap']`

**Markers**: Store as DataFrame or dict

### Platform-Specific Notes

**Xenium (10x)**:
- 300-gene panels
- Subcellular resolution
- Quality control on transcript counts

**AtlasXomics (ATAC-seq)**:
- Peaks × cells matrix
- Gene activity scores
- Motif analysis

**Vizgen (MERFISH)**:
- 500+ gene panels
- Cell segmentation from DAPI
- z-stack imaging

**Curio Seeker**:
- Beads, not cells
- Background removal important
- Spatial registration to H&E
