#!/bin/bash
set -e

EVAL_DIR="${1:-evals_full/seeker}"
OUTPUT_BASE="results"
PARALLEL_WORKERS="${2:-6}"
KEEP_WORKSPACE="${3:-true}"

MODELS=(
    "openai/gpt-5-codex"
    "anthropic/claude-sonnet-4-5"
)

MODEL_NAMES=(
    "gpt5codex"
    "sonnet45"
)

echo "=========================================="
echo "SpatialBench Multi-Model Benchmark"
echo "=========================================="
echo ""
echo "Evaluation directory: $EVAL_DIR"
echo "Output directory: $OUTPUT_BASE"
echo "Parallel workers: $PARALLEL_WORKERS"
echo ""
echo "Models to benchmark:"
for i in "${!MODELS[@]}"; do
    echo "  ${MODEL_NAMES[$i]}: ${MODELS[$i]}"
done
echo ""

read -p "Continue with benchmark? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Benchmark cancelled."
    exit 0
fi

BENCHMARK_START=$(date +%s)

for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    MODEL_NAME="${MODEL_NAMES[$i]}"
    OUTPUT_DIR="$OUTPUT_BASE/$MODEL_NAME"

    echo ""
    echo "=========================================="
    echo "Running benchmark for: $MODEL_NAME"
    echo "Model: $MODEL"
    echo "Output: $OUTPUT_DIR"
    echo "=========================================="
    echo ""

    START=$(date +%s)

    mkdir -p "$OUTPUT_DIR"

    KEEP_WS_FLAG=""
    if [[ "$KEEP_WORKSPACE" == "true" ]]; then
        KEEP_WS_FLAG="--keep-workspace"
    fi

    .venv/bin/python -m spatialbench.cli batch "$EVAL_DIR" \
        --agent minisweagent \
        --model "$MODEL" \
        --output "$OUTPUT_DIR" \
        --parallel "$PARALLEL_WORKERS" \
        $KEEP_WS_FLAG \
        2>&1 | tee "$OUTPUT_DIR/batch_log.txt"

    END=$(date +%s)
    DURATION=$((END - START))

    echo ""
    echo "Completed $MODEL_NAME in ${DURATION}s ($(($DURATION / 60))m)"
    echo ""
done

BENCHMARK_END=$(date +%s)
TOTAL_DURATION=$((BENCHMARK_END - BENCHMARK_START))

echo ""
echo "=========================================="
echo "Benchmark Complete!"
echo "=========================================="
echo "Total duration: ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60))m)"
echo ""
echo "Results saved to:"
for MODEL_NAME in "${MODEL_NAMES[@]}"; do
    echo "  $OUTPUT_BASE/$MODEL_NAME/batch_results.json"
done
echo ""
echo "To compare results, run:"
echo "  python scripts/compare_models.py $OUTPUT_BASE/"
echo ""
