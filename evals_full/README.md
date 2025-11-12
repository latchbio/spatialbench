# Full SpatialBench Evaluation Set

This directory contains the complete 98-evaluation benchmark for SpatialBench. It is organized by spatial biology technology platform.

## Directory Structure

```
evals_full/
├── xenium/          # 30 evaluations - 10x Genomics Xenium
├── vizgen/          # 31 evaluations - Vizgen MERFISH
├── atlasxomics/     # 25 evaluations - AtlasXomics spatial ATAC-seq
└── seeker/          # 12 evaluations - Curio Seeker
```

## Usage

**This directory is gitignored** to prevent the full benchmark from being publicly available, which would allow models to be specifically optimized for these tasks.

### Running the Full Benchmark

```bash
# Run all evaluations
spatialbench batch evals_full/ --agent minisweagent --output results/

# Run specific platform
spatialbench batch evals_full/xenium/ --agent minisweagent --output results/xenium/

# Run with specific model
spatialbench batch evals_full/ --agent minisweagent --model claude-3-5-sonnet-20241022 --output results/
```

### Adding Evaluations

Place evaluation JSON files in the appropriate technology subdirectory:

- **xenium/** - Xenium (10x) in situ sequencing data
- **vizgen/** - Vizgen MERFISH multiplexed imaging data
- **atlasxomics/** - AtlasXomics spatial ATAC-seq data
- **seeker/** - Curio Seeker bead-based spatial transcriptomics

Each evaluation file should follow the standard format (see `../evals/` for examples).

## Benchmark Composition

| Technology       | Evaluations | Description |
|------------------|-------------|-------------|
| Xenium           | 30          | 10x in situ sequencing, 300-500 gene panels |
| Vizgen (MERFISH) | 31          | Multiplexed FISH, 500+ gene panels |
| AtlasXomics      | 25          | Spatial ATAC-seq, epigenomics |
| Seeker/Curio     | 12          | Bead-based whole transcriptome capture |
| **Total**        | **98**      | Comprehensive spatial biology benchmark |

## Task Categories

The full benchmark spans six categories:

1. **Quality Control (QC)** - Dataset metrics, filtering criteria
2. **Preprocessing** - Normalization, dimensionality reduction, batch correction
3. **Clustering** - Algorithm selection, parameter tuning, spatial coherence
4. **Cell Type Annotation** - Marker-based typing, hierarchical classification
5. **Differential Expression** - Statistical testing, marker discovery
6. **Spatial Analysis** - Spatial statistics, tissue composition, cell interactions

## Access Control

This directory is maintained separately from the public repository examples (`evals/`) to:

- **Prevent overfitting** - Models cannot be tuned for specific benchmark tasks
- **Ensure valid comparisons** - All models evaluated on same unseen tasks
- **Maintain benchmark integrity** - Results reflect genuine capabilities
- **Enable research** - Published results are reliable and reproducible

For questions about the full benchmark, contact [kenny@latch.bio](mailto:kenny@latch.bio).
