# Evaluation Methodology

All evaluations were run using [latch-eval-tools](https://github.com/latchbio/latch-eval-tools). 

Full configuration details can be found in [latch-eval-tools](https://github.com/latchbio/latch-eval-tools). Generally models are run at max reasoning effort where applicable and no limits on the number of steps (i.e the number of api calls). 

Each evaluation is run 3 times and results are averaged (See [scripts/generate_model_results.py](scripts/generate_model_results.py) for more details). Each evaluation is run in a container with 4 vCPU,32GB RAM, and 100GB of storage and a task timeout of 21600 seconds (6 hours).  The evaluation environment itself is a Docker container with common libraries installed (See [agent_env](https://github.com/latchbio/latch-eval-tools/blob/main/agent_env/Dockerfile)). The mini-swe-agent harness run outside the evaluation container with tool calls executed inside the evaluation container. The Claude-Code and OpenAI-Codex binaries run inside the evaluation container. Note that while we discourage the models from downloading/searching for external libraries/datasets, we do not enforce this (the container has network access). We make this choice because spatial biology tasks frequently require access to external annotation libraries (eg: [gprofiler](https://biit.cs.ut.ee/gprofiler/)). An alternative choice would be to present curated annotation datasets as part of the packaged data to the model. We observe that even with these resources model sometimes hit out of memory errors. To mitigate this we detect when the container hits Out of Memory (OOM) errors and restart the agent with a warning message. 

All evaluations were run on the Latch platforms using [Workflows](https://wiki.latch.bio/workflows/overview). 

## Trajectories

The trajectories directory is structured as follows:
```
trajectories/
  <task_file_name>/
    <provider>/
      <model>/
        <harness>/
          <trial>/
            trajectory.json
            harness_outputs.jsonl
            result.json
            eval_answer.json
```

where:

- `task_file_name`: The stem (no extension)filename of the evaluation task. eg: `ct_04_excitatory_neuron_layer_identity`
- `provider`: The provider of the model. eg: `anthropic` or `openai`
- `model`: The model name. eg: `claude-sonnet-4-6` or `gpt-5.4`
- `harness`: The harness name. eg: `mini-swe-agent` or `claude-code` or `openai-codex`
- `trial`: The trial number. eg: `r1`, `r2`, `r3`
- `result.json`: The result of the evaluation. The grader output from `latch-eval-tools` along with some additional metadata.
- `trajectory.json`: The trajectory of the agent. For `mini-swe-agent` this is the output produced by the mini-swe-agent harness itself. For `claude-code` and `openai-codex` this is the output written to stdout by the respective binary. 
- `harness_outputs.jsonl`: Since the stdout output from Claude-Code and OpenAI-Codex does not contain some interesting information (timestamps) we separately collect the session rollout from the respective harness which is available in the `harness_outputs.jsonl` file. Note that this follows the respective harness(Claude-Code,OpenAI-Codex) output conventions and is not standardized.
- `eval_answer.json`: The answer produced by the agent.
