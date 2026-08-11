# Loop Engineering Course Redesign

## Purpose

Reposition Loop Engineering Study as both an executable course and a small,
reusable Python framework. The course must let a Python developer understand
and improve an AI/Agent-style iterative loop without requiring an API key,
network service, or production agent stack.

## Primary audience

The primary learner already writes Python and wants to understand iterative
AI/Agent loops systematically. They are not assumed to know how to design
evaluation, feedback, traces, or bounded stopping behavior.

## Core learning promise

Within 45 minutes, a learner can use Trace, evaluation evidence, and a
controlled comparison to diagnose why an Agent loop does not improve and make
one verifiable improvement.

By the end of the core course, the learner can:

1. Explain the responsibilities of state, action, evaluation, feedback, and
   stopping conditions in an iterative loop.
2. Read a Trace and distinguish an action failure, uninformative evaluation,
   ineffective feedback, and an unsuitable stopping rule.
3. Change exactly one loop component, compare it to a baseline, and use tests,
   metrics, and Trace evidence to justify the result.
4. Map the case back to the reusable `Policy`, `Action`, `Evaluator`,
   `WorkingMemory`, `StopCondition`, `LoopRunner`, and Artifact boundaries.

## Non-goals

- This repository is not a general-purpose agent platform, production
  orchestrator, or vendor SDK.
- The core lesson does not require an LLM, network access, arbitrary shell
  execution, or credentials.
- External model and local-tool integrations remain advanced extensions rather
  than prerequisites for understanding Loop Engineering.

## Course narrative

The canonical case is a code-repair Agent attempting to repair a failing Python
function. Its baseline run intentionally fails to repair reliably. The learner
does not begin by reading framework classes: they run the baseline, inspect its
Trace and evaluator evidence, form a diagnosis, then make a minimal controlled
change.

The 45-minute route has five parts:

| Time | Activity | Evidence produced |
| --- | --- | --- |
| 0-5 min | Run the failed baseline | initial Artifact, failing evaluation, stop reason |
| 5-15 min | Read the Trace | written diagnosis of the failed loop boundary |
| 15-30 min | Run three one-variable experiments | comparable Artifact and metric differences |
| 30-40 min | Improve one diagnosed boundary | passing case test plus before/after Trace |
| 40-45 min | Map the case to the framework | component-to-concept checklist |

The three required experiments are:

1. **Evaluation signal:** distinguish a candidate patch being applied from the
   Python behavior actually satisfying its tests.
2. **Feedback strategy:** transform evaluation evidence into a specific next
   repair choice instead of repeating an ineffective action.
3. **Stopping policy:** stop repeated ineffective attempts while preserving the
   reason and evidence for that decision.

Each experiment changes one factor only and produces a directly comparable
Artifact.

## Architecture and repository shape

The existing `loop_engineering/` package remains the domain-neutral framework.
It must not import code-repair-specific types. A deterministic code-repair
domain adapts its state, candidate patches, and test-style evaluator to the
framework's existing interfaces.

```text
README.zh-CN.md / README.md
  -> course/01-baseline.md
  -> course/02-read-the-trace.md
  -> course/03-improve-the-loop.md
  -> experiments/code_repair/
       baseline.py
       evaluator_signal.py
       feedback_strategy.py
       stopping_policy.py

examples/code_repair/
  failing_function.py
  candidate_repairs.py
  evaluator fixtures

loop_engineering/
  reusable Policy / Action / Evaluator / Memory / StopCondition / Runner /
  Trace / Artifact boundaries

docs/reference/
  framework and Artifact reference

docs/advanced/
  existing numeric, diagnosis, model-adapter, and local-tool material
```

The exact directory migration is part of implementation planning. Existing
numeric experiments remain available as minimal mechanism examples; they are
not the README's primary narrative. Existing advanced material is retained and
re-linked, not deleted.

## Public entry experience

The README must answer, before installation:

1. What failure does Loop Engineering address?
2. Who is this course for?
3. What can the learner do in 45 minutes?
4. What is the first command and what evidence should it produce?
5. How does the code-repair case map to the small reusable framework?

The Chinese README is the primary course entry. The English README accurately
describes the course, points to the Chinese-first materials, and gives a short
English orientation without pretending that the full course is translated.

## Verification and acceptance criteria

- A fresh local setup runs the baseline and all three experiments without
  credentials or network calls.
- The baseline's designated case fails deterministically.
- Each improved experiment has a deterministic expected outcome and produces
  an Artifact with Trace, final state, metrics, and stop reason.
- The learner's improvement case proves success through a test-style evaluator
  and a before/after Artifact comparison.
- Contract tests protect the README's audience, learning promise, first
  experiment link, and course-step links.
- Runtime tests continue to protect event order, artifact contracts, stopping
  boundaries, and existing deterministic examples.
- Documentation checks continue to validate UTF-8 and public local links.

## Migration constraints

- Maintain Python `>=3.11` support and an empty runtime dependency list.
- Preserve the deterministic, local-first baseline.
- Do not delete current experiments, historical development documents, or
  advanced adapters during this redesign.
- Do not create a GitHub Release, Git tag, or modify remote repository settings
  as part of this redesign.
