# Controlled Local Tool Adapter Design

## Goal

Add a learning-focused local tool adapter that runs explicitly registered, side-effect-free diagnostic commands and maps results into the existing ActionResult, Trace, Evaluator, and Artifact loop.

## Scope

The first phase supports only local subprocess tools:

- Explicit construction-time tool allowlist.
- Absolute executable, fixed arguments, absolute working directory, and timeout.
- Shell disabled, no dynamic arguments, no environment injection.
- Exit code, timeout, and bounded output summaries.
- One side-effect-free teaching experiment that runs the Python version command.

It does not support arbitrary shell commands, dynamic arguments, file-modifying tools, network tools, tool chains, or implicit CLI execution.

## Architecture

ToolAction accepts a Decision with a registered tool name and no parameters. It asks LocalToolAdapter to run the fixed command with subprocess.run and shell disabled. ToolExecution becomes ActionResult, after which the existing loop records ACT, evaluates, and persists its normal Artifact.

### loop_engineering/tool_adapters.py

The module provides:

- ToolAdapterError for registration, selection, and execution contract violations.
- ToolDefinition with name, executable, arguments, working_directory, and timeout_seconds.
- ToolExecution with success, exit_code, stdout, stderr, and duration_seconds.
- LocalToolAdapter(definitions, output_limit=1000).

Construction rules:

- Tool names are non-empty and unique.
- executable and working_directory are absolute paths.
- working_directory exists and is a directory.
- timeout_seconds and output_limit are greater than zero.

Execution uses fixed argv only:

~~~python
subprocess.run(
    [definition.executable, *definition.arguments],
    cwd=definition.working_directory,
    shell=False,
    capture_output=True,
    text=True,
    timeout=definition.timeout_seconds,
    check=False,
)
~~~

No external parameters are accepted or appended. stdout and stderr are separately truncated to output_limit characters. A timeout becomes a failed ToolExecution with exit_code equal to None.

### loop_engineering/tool_action.py

ToolAction(adapter) implements the existing Action interface:

- Decision name must be registered and parameters must equal an empty dictionary.
- It executes the named tool.
- It uses state.with_value(state.value) for both success and failure.
- ActionResult success maps tool success; cost maps duration_seconds.
- Output summaries do not enter the existing ACT Trace payload, preserving the current Artifact contract.

Non-zero exits and timeouts return success false instead of raising into LoopRunner. Unknown names, non-empty parameters, and invalid definitions raise ToolAdapterError.

## Safety and observability

The project registers no tools by default. The CLI and existing experiments do not execute subprocesses. Definitions are explicit; policies can select only their registered names.

The teaching experiment uses the current Python executable with fixed --version arguments and an output directory as its working directory. It does not modify project files or access the network. Its structured report may contain bounded output, exit code, and duration; the Artifact continues to contain only ActionResult success and cost.

## Verification

Tests cover:

1. Fixed allowlisted argv, working directory, and successful mapping.
2. Rejection of unknown names and non-empty Decision parameters.
3. Non-zero exit failure.
4. Timeout failure.
5. stdout and stderr truncation.
6. Duplicate names, relative paths, missing directories, and invalid timeout rejection.
7. ToolAction integration with LoopRunner and Artifact.
8. Stable no-side-effect teaching experiment report and replayable Artifact.

## Documentation and acceptance

Add a tool adapter guide covering the diagnostic-only boundary, registration, Trace behavior, and unsupported capabilities. Link it from experiments, README learning paths, and progress.

Acceptance criteria:

- Commands use fixed registered argv and shell false.
- Failures are observable by the existing loop without leaking output into Artifact.
- Normal project use executes no tools.
- The teaching experiment does not write project files or call the network.
- Full pytest passes.

