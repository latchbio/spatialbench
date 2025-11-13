# CLI Usage Guide

SpatialBench provides a command-line interface for running evaluations and managing benchmarks.

## Commands

### run - Run a single evaluation

```bash
spatialbench run <eval_path> [options]
```

**Options:**
- `--agent minisweagent` - Use mini-swe-agent to run the evaluation
- `--model <model>` - Specify model name (e.g., `anthropic/claude-sonnet-4-5`, `openai/gpt-4o`)
- `--keep-workspace` - Keep workspace directory after completion
- `--verbose, -v` - Verbose output

**Examples:**

```bash
spatialbench run evals/qc/seeker_qc_basic.json --agent minisweagent

spatialbench run evals/qc/seeker_qc_basic.json \
  --agent minisweagent \
  --model anthropic/claude-sonnet-4-5 \
  --keep-workspace
```

### batch - Run multiple evaluations

```bash
spatialbench batch <eval_dir> [options]
```

**Options:**
- `--agent minisweagent` - Use mini-swe-agent for all evaluations
- `--model <model>` - Model name for agent
- `--output, -o <dir>` - Output directory for results
- `--parallel, -p <n>` - Number of parallel workers (default: 1)
- `--keep-workspace` - Keep workspace after each eval

**Examples:**

```bash
spatialbench batch evals_full/seeker --agent minisweagent

spatialbench batch evals_full/seeker \
  --agent minisweagent \
  --model anthropic/claude-sonnet-4-5 \
  --output results/run1 \
  --parallel 6 \
  --keep-workspace
```

**Batch Process:**

1. **Dataset collection** - Scans all eval files and collects unique dataset URIs
2. **Batch download** - Downloads all datasets upfront (if using Latch data nodes)
3. **Parallel execution** - Runs evaluations with specified number of workers
4. **Result aggregation** - Collects results and computes summary statistics

**Batch Results:**

Results are saved to `<output_dir>/batch_results.json`:

```json
{
  "metadata": {
    "model": "anthropic/claude-sonnet-4-5",
    "timestamp": "2025-01-12T21:30:45Z",
    "total_evals": 12,
    "passed": 10,
    "failed": 2,
    "pass_rate": 83.3,
    "avg_duration_s": 45.2,
    "total_cost": 0.34,
    "avg_cost_per_eval": 0.028,
    "total_steps": 38,
    "avg_steps_per_eval": 3.2
  },
  "results": [
    {
      "eval": "curio_mt_percentage.json",
      "passed": true,
      "test_id": "curio_mt_percentage",
      "model": "anthropic/claude-sonnet-4-5",
      "timestamp": "2025-01-12T21:31:15Z",
      "duration_s": 42.3,
      "total_cost": 0.028,
      "n_steps": 3,
      "n_messages": 6
    }
  ]
}
```

### validate - Validate evaluation format

```bash
spatialbench validate <eval_path>
```

Checks that an evaluation file:
- Contains required fields (`id`, `task`)
- Uses a valid grader type
- Has valid JSON syntax

**Example:**

```bash
spatialbench validate evals/qc/seeker_qc_basic.json
```

### list - List available evaluations

```bash
spatialbench list [--category <category>]
```

Lists all evaluations in the package, optionally filtered by category.

**Categories:**
- `qc` - Quality control
- `preprocessing` - Normalization, dimensionality reduction
- `clustering` - Clustering algorithms
- `cell_typing` - Cell type annotation
- `differential_expression` - Marker gene discovery
- `spatial_analysis` - Spatial-specific analyses

**Example:**

```bash
spatialbench list
spatialbench list --category qc
```

## Environment Variables

### Model Configuration

**For Anthropic models:**
```bash
export MSWEA_MODEL_NAME=anthropic/claude-sonnet-4-5
export ANTHROPIC_API_KEY=your_api_key
```

**For OpenAI models:**
```bash
export MSWEA_MODEL_NAME=openai/gpt-4o
export OPENAI_API_KEY=your_api_key
```

**Supported Models:**
- `anthropic/claude-sonnet-4-5` - Claude Sonnet 4.5 (recommended)
- `anthropic/claude-opus-4` - Claude Opus 4
- `openai/gpt-4o` - GPT-4o
- `openai/gpt-4o-mini` - GPT-4o Mini
- `openai/o1` - OpenAI o1
- `openai/o1-mini` - OpenAI o1 Mini

### Latch Configuration

If using Latch data nodes:
```bash
export LATCH_TOKEN=your_latch_token
```

## Programmatic Usage

For more control, use the Python API:

```python
from spatialbench import EvalRunner
from spatialbench.harness import run_minisweagent_task

runner = EvalRunner(
    "evals/qc/seeker_qc_basic.json",
    keep_workspace=True
)

result = runner.run(
    agent_function=lambda task, work_dir: run_minisweagent_task(
        task,
        work_dir,
        model_name="anthropic/claude-sonnet-4-5"
    )
)

print(f"Passed: {result['passed']}")
print(f"Cost: ${result['metadata']['total_cost']:.4f}")
print(f"Steps: {result['metadata']['n_steps']}")
```

## Monitoring Batch Runs

See [BATCH_MONITORING.md](../BATCH_MONITORING.md) for detailed instructions on:
- Real-time progress monitoring
- Identifying stuck evaluations
- Viewing agent logs
- Performance metrics
- Troubleshooting common issues

## Benchmark Script

For running multi-model benchmarks:

```bash
./scripts/benchmark_models.sh <eval_dir> [workers] [keep_workspace]
```

This script:
- Runs multiple models on the same eval set
- Organizes results by timestamp: `results/run_TIMESTAMP/`
- Produces separate results for each model
- Includes timing and cost comparisons

**Example:**

```bash
./scripts/benchmark_models.sh evals_full/seeker 6 true
```

Results will be saved to:
```
results/
  run_20250112_213045/
    sonnet45/
      batch_results.json
      batch_log.txt
    gpt5codex/
      batch_results.json
      batch_log.txt
```
