# Public release checklist

Use this checklist before publishing a learning-oriented release. It records
the release decision without creating a tag or GitHub Release automatically.

## Verify the repository

- [ ] Install from a clean environment with `python -m pip install -e ".[dev]"`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m build --wheel`.
- [ ] Run `python scripts/check_docs.py`.
- [ ] Run the 45-minute course experiments:
  `python experiments/code_repair/baseline.py`,
  `python experiments/code_repair/evaluator_signal.py`,
  `python experiments/code_repair/feedback_strategy.py`, and
  `python experiments/code_repair/stopping_policy.py`.
- [ ] Compare the baseline and feedback Artifacts with
  `python -m loop_engineering.cli compare .loop/runs/code-repair/baseline.json .loop/runs/code-repair/feedback_strategy.json`.
- [ ] Confirm no generated `.loop/` artifacts, coverage data, credentials, or
  local environments are staged.

## Prepare the GitHub repository

- [ ] Confirm the repository is publicly visible to the intended audience.
- [ ] Set a concise description and relevant topics such as `loop-engineering`,
  `python`, `learning`, `experiments`, and `agent-systems`.
- [ ] Check the rendered English and Chinese README pages in GitHub.
- [ ] Confirm the license, contribution guide, code of conduct, and security
  policy remain visible.

## Create the release

- [ ] Choose a semantic version and create the matching annotated Git tag.
- [ ] Create a GitHub Release using the matching tag.
- [ ] Summarize learner-visible changes, known limits, and the deterministic,
  local-first baseline in the release notes.
- [ ] Link the beginner route and invite focused issues or pull requests.
