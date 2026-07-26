# External Model Reliability Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic retry, exponential backoff, and per-adapter circuit breaking to external HTTP model calls without changing the Loop, Trace, Artifact, or ModelPolicy contracts.

**Architecture:** Extend `HttpModelAdapter` with an immutable `ReliabilityPolicy`, injectable monotonic clock/sleeper, and private circuit state. The adapter retries only classified transport failures and raises `ModelAdapterError` on every exhausted or blocked path. A no-network experiment injects scripted transport and time doubles to show recovery and circuit transitions.

**Tech Stack:** Python 3.11+, standard library (`dataclasses`, `time`, `urllib`), pytest.

## Global Constraints

- Preserve the existing `HttpTransport.post_json(...) -> HttpResponse` and `ModelPolicy -> complete() -> Decision` interfaces.
- Default reliability values are `max_attempts=3`, `base_delay_seconds=0.1`, `failure_threshold=3`, and `cooldown_seconds=30.0`.
- Retry only `URLError`, socket timeout/other `OSError`, HTTP `429`, and HTTP `500` through `599`.
- Do not retry other `4xx`, invalid JSON, or a response that violates the existing Decision contract.
- Use `base_delay_seconds × 2^retry_index`; do not add random jitter.
- The circuit is per adapter instance and follows `closed -> open -> half-open -> closed`.
- Open circuits must reject calls without invoking the transport; half-open permits one probe only.
- A half-open probe performs exactly one transport call and does not consume the normal retry budget; a retryable probe failure reopens the circuit immediately.
- No fallback policy, fabricated Decision, API-key/request/response persistence, environment-variable read, vendor SDK, Trace change, or Artifact change.
- All error messages and `reliability_snapshot()` values must exclude API Key, endpoint, model name, request body, and response body.

---

## File Structure

- Modify: `loop_engineering/model_adapters.py` — reliability configuration, failure classification, retry loop, circuit state, and sanitized snapshot.
- Modify: `tests/test_model_adapters.py` — retry, error-classification, circuit, snapshot, and compatibility tests.
- Create: `experiments/external_model_reliability.py` — no-network scripted reliability scenarios and replayable reports.
- Create: `tests/test_external_model_reliability.py` — stable experiment report and Artifact verification.
- Create: `docs/external-model-reliability.md` — Chinese learner guide for retry and circuit behavior.
- Modify: `docs/external-model-adapter.md` — link the production-reliability extension and retain the explicit external boundary.
- Modify: `docs/experiments.md` — add the experiment command and description.
- Modify: `README.md` and `README.zh-CN.md` — add learning-path entries.
- Modify: `docs/architecture.md` — describe the optional reliable model-call boundary.
- Modify: `docs/superpowers/sdd/progress.md` — record the exact verified test count.

### Task 1: Reliability configuration, failure classification, and deterministic retry

**Files:**
- Modify: `loop_engineering/model_adapters.py`
- Modify: `tests/test_model_adapters.py`

**Interfaces:**
- Produces: `ReliabilityPolicy(max_attempts=3, base_delay_seconds=0.1, failure_threshold=3, cooldown_seconds=30.0)`.
- Produces: extended `HttpModelAdapter(..., reliability_policy=None, clock=time.monotonic, sleeper=time.sleep)`.
- Preserves: `HttpModelAdapter.complete(input_payload: dict[str, object]) -> Decision`.

- [ ] **Step 1: Write failing retry and validation tests**

```python
def test_adapter_retries_429_with_deterministic_backoff() -> None:
    transport = ScriptedTransport([
        HttpResponse(429, "busy"),
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": 2}}'),
    ])
    sleeps: list[float] = []
    adapter = HttpModelAdapter(
        "https://models.example.test", "model", "", transport,
        reliability_policy=ReliabilityPolicy(max_attempts=3, base_delay_seconds=0.25),
        sleeper=sleeps.append,
    )

    assert adapter.complete({}).parameters == {"amount": 2.0}
    assert transport.call_count == 2
    assert sleeps == [0.25]
```

Add tests for a `URLError` and `TimeoutError` retrying with `[0.1, 0.2]`, `400` and invalid JSON making exactly one call with no sleeps, exhausted `503` raising a sanitized `ModelAdapterError`, and every invalid `ReliabilityPolicy` field raising `ModelAdapterError` at construction.

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_model_adapters.py -v`

Expected: FAIL during collection because `ReliabilityPolicy` does not exist.

- [ ] **Step 3: Implement configuration and the minimal retry loop**

```python
@dataclass(frozen=True)
class ReliabilityPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.1
    failure_threshold: int = 3
    cooldown_seconds: float = 30.0

def complete(self, input_payload: dict[str, object]) -> Decision:
    self._before_call()
    max_attempts = 1 if self._circuit_state == "half-open" else self.reliability_policy.max_attempts
    for attempt in range(max_attempts):
        try:
            response = self.transport.post_json(...)
            if self._is_retryable_status(response.status_code):
                raise _RetryableModelFailure(response.status_code)
            decision = self._decision_from_response(response)
        except _RetryableModelFailure as error:
            self._record_retryable_failure()
            if attempt + 1 == max_attempts:
                raise ModelAdapterError(error.summary(attempt + 1)) from error
            self.sleeper(self.reliability_policy.base_delay_seconds * (2**attempt))
            continue
        self._record_success()
        return decision
```

Keep response decoding and Decision validation in helpers so invalid JSON and invalid decision payloads remain non-retryable. Translate transport-layer exceptions to a private retryable error with a category-only message; never incorporate exception text, response body, endpoint, model, or API key into public errors.

- [ ] **Step 4: Run retry tests to verify they pass**

Run: `python -m pytest tests/test_model_adapters.py -v`

Expected: PASS.

- [ ] **Step 5: Commit retry controls**

```bash
git add loop_engineering/model_adapters.py tests/test_model_adapters.py
git commit -m "feat: add model adapter retry controls"
```

### Task 2: Circuit state machine and safe reliability snapshots

**Files:**
- Modify: `loop_engineering/model_adapters.py`
- Modify: `tests/test_model_adapters.py`

**Interfaces:**
- Consumes: `ReliabilityPolicy`, retryable-failure recording, and injected `clock` from Task 1.
- Produces: `HttpModelAdapter.reliability_snapshot() -> dict[str, object]` with keys `state`, `consecutive_failures`, and `next_probe_at`.

- [ ] **Step 1: Write failing circuit-transition tests**

```python
def test_open_circuit_rejects_without_transport_call() -> None:
    now = [10.0]
    transport = ScriptedTransport([HttpResponse(503, "down")] * 3)
    adapter = HttpModelAdapter(
        "https://models.example.test", "model", "secret", transport,
        reliability_policy=ReliabilityPolicy(max_attempts=1, failure_threshold=3, cooldown_seconds=30.0),
        clock=lambda: now[0], sleeper=lambda seconds: None,
    )

    for _ in range(3):
        with pytest.raises(ModelAdapterError):
            adapter.complete({})
    calls_before = transport.call_count
    with pytest.raises(ModelAdapterError, match="circuit"):
        adapter.complete({})

    assert transport.call_count == calls_before
    assert adapter.reliability_snapshot() == {
        "state": "open", "consecutive_failures": 3, "next_probe_at": 40.0,
    }
```

Add tests advancing `now[0]` to prove exactly one half-open probe succeeds and resets to `closed`, a failed half-open probe returns to `open` with a refreshed cooldown, and snapshots/errors never contain the supplied secret, endpoint, model, payload, or response text.

- [ ] **Step 2: Run circuit tests to verify they fail**

Run: `python -m pytest tests/test_model_adapters.py -k "circuit or snapshot" -v`

Expected: FAIL because the circuit and snapshot methods do not exist.

- [ ] **Step 3: Implement circuit guarding and state transitions**

```python
def _before_call(self) -> None:
    if self._circuit_state != "open":
        return
    if self.clock() < self._opened_at + self.reliability_policy.cooldown_seconds:
        raise ModelAdapterError("Model circuit is open")
    self._circuit_state = "half-open"

def _record_success(self) -> None:
    self._circuit_state = "closed"
    self._consecutive_failures = 0
    self._opened_at = None

def reliability_snapshot(self) -> dict[str, object]:
    next_probe_at = None
    if self._circuit_state == "open" and self._opened_at is not None:
        next_probe_at = self._opened_at + self.reliability_policy.cooldown_seconds
    return {"state": self._circuit_state, "consecutive_failures": self._consecutive_failures, "next_probe_at": next_probe_at}
```

When the unique half-open probe has a retryable failure, reopen immediately. In `closed`, open only after the configured consecutive-failure threshold. Do not alter the counter for non-retryable errors.

- [ ] **Step 4: Run circuit and complete adapter tests to verify they pass**

Run: `python -m pytest tests/test_model_adapters.py -v`

Expected: PASS.

- [ ] **Step 5: Commit circuit controls**

```bash
git add loop_engineering/model_adapters.py tests/test_model_adapters.py
git commit -m "feat: add model adapter circuit breaker"
```

### Task 3: No-network teaching experiment and documentation

**Files:**
- Create: `experiments/external_model_reliability.py`
- Create: `tests/test_external_model_reliability.py`
- Create: `docs/external-model-reliability.md`
- Modify: `docs/external-model-adapter.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: `HttpModelAdapter`, `HttpResponse`, `ReliabilityPolicy`, `ModelPolicy`, and Artifact helpers.
- Produces: `run_external_model_reliability_demo(output_dir: str | Path = ".loop/runs/external-model-reliability") -> dict[str, object]`.

- [ ] **Step 1: Write the failing experiment test**

```python
def test_reliability_demo_is_network_free_and_replayable(tmp_path: Path) -> None:
    report = run_external_model_reliability_demo(tmp_path)

    assert report["retry_then_success"]["sleep_seconds"] == [0.1]
    assert report["retry_then_success"]["status"] == "SUCCEEDED"
    assert report["open_circuit"]["blocked_transport_calls"] == 0
    assert report["half_open_success"]["final_snapshot"]["state"] == "closed"
    artifact_path = Path(report["retry_then_success"]["artifact_path"])
    trace, metrics = load_run_artifact(artifact_path)
    assert metrics.success is True
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == report
```

- [ ] **Step 2: Run the experiment test to verify it fails**

Run: `python -m pytest tests/test_external_model_reliability.py -v`

Expected: FAIL during collection because `experiments.external_model_reliability` does not exist.

- [ ] **Step 3: Implement the scripted no-network experiment**

```python
class ScriptedTransport:
    def __init__(self, outcomes: list[HttpResponse | Exception]) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        del endpoint, headers, payload, timeout_seconds
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
```

Use local mutable clocks and `sleep_seconds.append` callbacks. Build one replayable success loop for `429 -> 200`; run separate direct adapter scenarios for open-circuit rejection and half-open success. Write only `artifact.json` and `report.json` under the caller-provided output directory. Do not put model request/response bodies, endpoints, model names, or secrets in the report.

- [ ] **Step 4: Write learner documentation and project links**

Create the Chinese guide with the exact retryable set, `base_delay_seconds × 2^retry_index` formula, default values, state transitions, explicit failure behavior, snapshot fields, and unsupported production capabilities. Link it from the existing external-model guide, experiments index, both READMEs, and architecture page. Keep the existing statement that normal project runs use no network.

- [ ] **Step 5: Run focused, script, and full verification**

Run: `python -m pytest tests/test_model_adapters.py tests/test_external_model_reliability.py -v`

Expected: PASS.

Run: `python experiments/external_model_reliability.py`

Expected: JSON report for retry recovery, open-circuit rejection, and successful half-open probe; no network call occurs.

Run: `python -m pytest -q`

Expected: PASS for the full project suite.

- [ ] **Step 6: Record exact test count and commit the learning surface**

Update `docs/superpowers/sdd/progress.md` with the exact full-suite count from Step 5. Re-run `python -m pytest -q` after the documentation edit.

```bash
git add experiments/external_model_reliability.py tests/test_external_model_reliability.py docs/external-model-reliability.md docs/external-model-adapter.md docs/experiments.md README.md README.zh-CN.md docs/architecture.md docs/superpowers/sdd/progress.md
git commit -m "docs: add model reliability learning experiment"
```

## Self-Review

- Spec coverage: Task 1 covers configuration validation, classified retries, fixed backoff, and explicit exhausted errors. Task 2 covers all circuit states, no-call open rejection, half-open behavior, and sanitized snapshots. Task 3 covers the no-network experiment, Artifact replay, project documentation, and full verification.
- Placeholder scan: every task includes concrete files, interfaces, test commands, expected outcomes, and implementation guidance.
- Type consistency: `ReliabilityPolicy` and extended `HttpModelAdapter` are defined in Task 1; Task 2 adds `reliability_snapshot`; Task 3 consumes those exact interfaces.
