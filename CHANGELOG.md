# Changelog

## [Unreleased]

### Fixed

#### Graders
- Fixed all graders to implement `evaluate_answer()` instead of `evaluate()` to work with the runner's direct answer passing:
  - `LabelSetJaccardGrader`
  - `DistributionComparisonGrader`
  - `MarkerGenePrecisionRecallGrader`
  - `MarkerGeneSeparationGrader`
  - `SpatialAdjacencyGrader`
- `NumericToleranceGrader` was already correct

#### Package
- Added `[tool.setuptools.packages.find]` to pyproject.toml to fix "multiple top-level packages" error during installation

### Changed

#### Evals
- Updated `label_set_jaccard` evals to use consistent config format:
  - `xenium_kidney_typing.json`: Added explicit `cell_types_predicted` field requirement to task
  - `vizgen_de_temporal.json`: Changed from `ground_truth_marker_sets` to `ground_truth_labels`, updated task to request `cell_types_predicted`
  - `vizgen_tissue_composition.json`: Changed from `ground_truth_marker_sets` to `ground_truth_labels`, updated task to request `cell_types_predicted`

#### Documentation
- Changed installation instructions from `pip install spatialbench` to `pip install -e .` in README.md
