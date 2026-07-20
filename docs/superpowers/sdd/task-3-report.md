# Task 3 Report

## Scope

Added the pluggable policy, action, and evaluator contracts plus their numeric
implementations. No runner, stopping condition, memory, metrics, CLI, or
experiment code was added.

## Evaluation rule

`GoalEvaluator` records `absolute_error` as a signal and uses
`1 / (1 + absolute_error)` as its score. This gives an exact hit a score of
`1.0` and keeps scores non-negative while decreasing monotonically as error
grows.

## Test status

Testing was attempted with `python -m pytest` and `py -3 -m pytest`. The first
command was unavailable and the Python launcher reported that no Python was
installed, so tests could not be executed in this workspace.
