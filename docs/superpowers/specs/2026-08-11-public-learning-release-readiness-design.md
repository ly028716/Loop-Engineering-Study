# Public Learning Release Readiness Design

## Goal

Make the repository easier to publish and learn from without expanding the
Loop Engineering runtime or changing its deterministic baseline.

## Decisions

1. The development extra must install every command documented for local
   verification. `build` therefore belongs in the `dev` extra alongside
   `pytest`.
2. The repository is Chinese-first for detailed learning material. The English
   README remains a concise project introduction and explicitly links readers
   to the Chinese learning path and README.
3. The main README presents a short beginner route first, then groups the
   complete experiment catalogue and reference material as advanced study.
4. A small, real Trace excerpt explains the observable loop before a reader
   installs the project.
5. Release work creates a local checklist only. It does not create a Git tag,
   GitHub Release, or alter repository settings.
6. Existing `docs/superpowers/` specifications, plans, and reports remain in
   place as development archives; an index explains that they are not part of
   the beginner curriculum.
7. A standard-library documentation check validates UTF-8 decoding, local
   Markdown targets, and the public README's essential entry points. CI runs
   this check before the test matrix.

## Verification

- Focused tests cover development dependency metadata and documentation-check
  behavior.
- The documentation checker exits successfully for the repository.
- The existing test suite, wheel build, semantic gate, and basic learning
  experiments remain runnable.

## Boundaries

- Python remains `>=3.11`.
- The baseline keeps no runtime dependencies and no network access.
- No historical document is deleted or moved.
