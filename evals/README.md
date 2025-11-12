# SpatialBench Example Evaluations

This catalog describes the example evaluations included in this repository. These represent samples across the major task categories from the full SpatialBench benchmark.

## Full Benchmark Scale

The complete SpatialBench benchmark comprises **98 evaluations**:

| Technology       | Evaluations |
|------------------|-------------|
| Xenium           | 30          |
| Vizgen (MERFISH) | 31          |
| AtlasXomics      | 25          |
| Seeker/Curio     | 12          |
| **Total**        | **98**      |

## Example Evaluations (This Repository)

This repository contains **7 representative examples** across the major task categories:

- **Platforms**: Xenium (10x), Vizgen (MERFISH), Curio Seeker
- **Categories**: QC, Preprocessing, Clustering, Cell Typing, Differential Expression, Spatial Analysis

**Note**: The full benchmark is withheld to prevent overfitting. These examples demonstrate the evaluation format, grading system, and task diversity without compromising benchmark integrity.

---

## Quality Control (QC)

### seeker_qc_basic

**Platform**: Curio Seeker
**Grader**: NumericToleranceGrader

Calculate basic QC metrics for Curio Seeker spatial transcriptomics data. Seeker uses bead-based capture (not cells), so terminology differs from cell-based platforms.

**Tests**:
- Basic data exploration
- Statistical summary calculations
- Understanding of bead-based QC metrics

**Key Metrics**: `on_tissue_beads`, `mean_genes_per_bead`, `median_genes_per_bead`, `std_genes_per_bead`

**Platform Notes**: Seeker captures RNA on beads rather than segmenting individual cells, requiring different QC considerations.

---

## Preprocessing

### xenium_normalization

**Platform**: Xenium (10x)
**Grader**: NumericToleranceGrader

Apply total count normalization and log transformation to spatial data.

**Tests**:
- Standard preprocessing pipeline
- Understanding of normalization (target_sum=1e4)
- log1p transformation

**Key Metrics**: `mean_sum_per_cell`, `max_value`, `min_value`

**Reference**: Scanpy normalization workflow

---

## Clustering

### xenium_leiden

**Platform**: Xenium (10x)
**Grader**: NumericToleranceGrader

Perform Leiden clustering on batch-corrected PCA embeddings from Xenium kidney data.

**Tests**:
- Graph construction (k-NN)
- Leiden clustering with specific resolution
- Cluster size distribution metrics
- Shannon entropy calculation

**Key Metrics**: `n_clusters`, `largest_cluster_frac`, `cluster_size_entropy`

**Challenges**:
- Using pre-computed harmony-corrected PCs
- Specific parameters (resolution=1.2, random_state=0)
- Calculating cluster statistics and entropy

---

## Cell Type Annotation

### xenium_kidney_typing

**Platform**: Xenium (10x)
**Grader**: LabelSetJaccardGrader

Assign each cell to one of 20 kidney cell type populations using a 300-gene Xenium panel.

**Tests**:
- Marker-based cell typing
- Biological knowledge (kidney cell types)
- Exact vocabulary matching

**Cell Types**: Pod, Glom-EC, EC, PTS1, PTS2, PTS3, Inj_PT, FR_PT, DTL, TAL, DCT, CNT, PC, ICA, ICB, Uro, PEC, Fib, Per-SMC, Immune

**Key Metrics**: `cell_types_predicted` (must match all 20 exactly)

**Reference**: Kidney cell type hierarchies

---

## Differential Expression

### vizgen_de_temporal

**Platform**: Vizgen (MERFISH)
**Grader**: LabelSetJaccardGrader

Perform temporal differential expression comparing aging (90wk) vs juvenile (4wk) astrocytes in mouse brain.

**Tests**:
- Cell type subsetting (astrocytes only)
- Two-group t-test (OLD vs JUVENILE)
- Gene ranking by logFC and adjusted p-value
- Gene symbol standardization (uppercase, deduplication)

**Key Metrics**: `markers_predicted` (top-13 OLD-upregulated genes)

**Canonical Markers**: GFAP, VIM, C4B, C3, SERPINA3N, CXCL10, IL18, HIF3A (aging/activated astrocyte markers)

**Scoring**: Jaccard ≥ 0.50 required

**Challenges**:
- Cell type-specific analysis
- Temporal comparison within cell type
- Gene symbol processing (remove Ensembl IDs)

---

## Spatial Analysis

### seeker_spatial_contiguity

**Platform**: Curio Seeker
**Grader**: NumericToleranceGrader

Perform clustering and measure spatial contiguity by calculating fragmentation. Tests whether clusters are spatially coherent or scattered.

**Tests**:
- Spatial clustering
- Connected components analysis
- Graph-based spatial metrics
- Fragmentation quantification

**Key Metrics**: `avg_fragmentation` (lower = more spatially contiguous clusters)

**Method**: For each cluster, count connected components where beads within 50μm distance are connected. Calculate weighted average fragmentation across all clusters.

**Challenges**:
- Spatial graph construction
- Connected components algorithm
- Understanding spatial quality metrics
- Balancing cluster purity vs spatial coherence

### vizgen_tissue_composition

**Platform**: Vizgen (MERFISH)
**Grader**: LabelSetJaccardGrader

Identify astrocyte clusters and extract marker genes from mouse brain MERFISH data.

**Tests**:
- One-vs-all differential expression (t-test)
- Marker gene ranking
- Cell type identification
- Gene symbol processing

**Key Metrics**: `markers_predicted` (top astrocyte markers)

**Canonical Markers**: GFAP, VIM, C4B, C3, SERPINA3N, CXCL10, IL18, HIF3A

**Scoring**: Jaccard ≥ 0.50 (using top-13 predicted markers)

**Challenges**:
- Multiple astrocyte clusters may exist
- Gene symbol standardization (uppercase, deduplication)
- Ranking by logFC and -log₁₀(p_adj)

---

## Platform Coverage

### Xenium (10x Genomics)

- **Technology**: Spatial transcriptomics, in situ sequencing
- **Panel Size**: 300-500 genes
- **Resolution**: Subcellular
- **Evaluations**: 3 (Preprocessing, Clustering, Cell Typing)

### Vizgen (MERFISH)

- **Technology**: Multiplexed FISH
- **Panel Size**: 500+ genes
- **Resolution**: Single-cell
- **Evaluations**: 2 (Differential Expression, Spatial Analysis)

### Curio Seeker (Takara Bio)

- **Technology**: Bead-based spatial capture
- **Panel Size**: Whole transcriptome
- **Resolution**: ~10μm beads (not single-cell)
- **Evaluations**: 2 (QC, Spatial Analysis)
- **Key Feature**: Captures RNA on spatially-barcoded beads, requires H&E registration

---

## Task Type Distribution

| Category | Example Count |
|----------|---------------|
| QC | 1 |
| Preprocessing | 1 |
| Clustering | 1 |
| Cell Typing | 1 |
| Differential Expression | 1 |
| Spatial Analysis | 2 |

---

## Grader Distribution

| Grader | Usage Count | Categories |
|--------|-------------|------------|
| NumericTolerance | 3 | QC, Preprocessing, Clustering |
| LabelSetJaccard | 3 | Cell Typing, DE, Spatial |
| DistributionComparison | 0 | - |
| MarkerGenePrecisionRecall | 0 | - |
| MarkerGeneSeparation | 0 | - |
| SpatialAdjacency | 0 | - |

---

## Benchmark Access

To obtain access to the full 98-evaluation benchmark for official model evaluation:

1. **Review the examples** in this repository to understand the format
2. **Contact**: [kenny@latch.bio](mailto:kenny@latch.bio) for benchmark access
3. **Submit results** following the guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md)

**Why is the full benchmark withheld?**

Making all evaluations public would allow models to be specifically optimized for the benchmark tasks, undermining the assessment of genuine spatial biology reasoning. The withheld evaluations ensure that reported performance reflects true capabilities rather than overfitting.

---

## Usage

Run a single evaluation:

```python
from spatialbench import EvalRunner

runner = EvalRunner("evals/qc/xenium_qc_basic.json")
result = runner.run(agent_function=my_agent)
```

Run all evaluations in a category:

```bash
spatialbench batch evals/cell_typing/ --model my-model
```

Run the entire benchmark:

```bash
spatialbench batch evals/ --model my-model
```

---

## Using These Examples

These example evaluations can help you:

1. **Understand the format**: See how tasks are specified and graded
2. **Test your harness integration**: Verify your agent can parse tasks and write outputs
3. **Develop locally**: Build and test your spatial biology agent
4. **Prepare for benchmark**: Ensure your system works before full evaluation

**Note**: Performance on these 7 examples does not predict performance on the full 98-evaluation benchmark. Submit to the official benchmark for comprehensive assessment.
