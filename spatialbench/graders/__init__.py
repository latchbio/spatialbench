from spatialbench.graders.base import BinaryGrader, GraderResult
from spatialbench.graders.numeric import NumericToleranceGrader
from spatialbench.graders.label_set import LabelSetJaccardGrader
from spatialbench.graders.distribution import DistributionComparisonGrader
from spatialbench.graders.marker_gene import MarkerGenePrecisionRecallGrader, MarkerGeneSeparationGrader
from spatialbench.graders.spatial import SpatialAdjacencyGrader
from spatialbench.graders.multiple_choice import MultipleChoiceGrader

GRADER_REGISTRY = {
    "numeric_tolerance": NumericToleranceGrader,
    "label_set_jaccard": LabelSetJaccardGrader,
    "distribution_comparison": DistributionComparisonGrader,
    "marker_gene_precision_recall": MarkerGenePrecisionRecallGrader,
    "marker_gene_separation": MarkerGeneSeparationGrader,
    "spatial_adjacency": SpatialAdjacencyGrader,
    "multiple_choice": MultipleChoiceGrader,
}

__all__ = [
    "BinaryGrader",
    "GraderResult",
    "NumericToleranceGrader",
    "LabelSetJaccardGrader",
    "DistributionComparisonGrader",
    "MarkerGenePrecisionRecallGrader",
    "MarkerGeneSeparationGrader",
    "SpatialAdjacencyGrader",
    "MultipleChoiceGrader",
    "GRADER_REGISTRY",
]
