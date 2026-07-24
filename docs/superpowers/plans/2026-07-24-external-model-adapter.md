# 外部 HTTP 模型适配层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以显式配置、可替换 HTTP transport 和严格 JSON 契约，将外部 HTTPS 模型输出接入现有 `Policy -> Decision` 循环边界。

**Architecture:** 新建 `model_adapters.py` 负责端点校验、HTTP 请求与响应解析；新建 `model_policy.py` 仅把 Loop 领域对象转换为适配器输入。真实 transport 使用标准库 `urllib.request`，测试和教学实验均注入假 transport，默认运行不会访问网络。

**Tech Stack:** Python 3.11、标准库 `urllib.request`/`json`/`dataclasses`/`math`、pytest。

## Global Constraints

- 仅接受显式 `endpoint`、`model`、`api_key` 和可选 `timeout_seconds`；不读取环境变量。
- 仅接受 `https://` endpoint；默认超时为 10 秒。
- 不将 endpoint、请求正文或 API Key 写入 Trace、Artifact、stdout 或 `ModelAdapterError`。
- 只在 `api_key` 非空时设置 `Authorization: Bearer <api_key>`；始终设置 `Content-Type: application/json`。
- 成功响应必须严格为 `{"name": str, "parameters": {str: finite number}}`，并转换为现有 `Decision`。
- 不改动 `LoopRunner`、`Action`、Artifact JSON 格式或默认 CLI `run` 行为。
- 所有功能遵循 TDD；每任务完成后运行指定测试并提交。

---

## File structure

- `loop_engineering/model_adapters.py`：适配器错误、HTTP 值对象/协议、urllib transport、请求验证与 Decision 解析。
- `loop_engineering/model_policy.py`：将 `LoopState`、`Feedback`、事件映射为适配器输入的 `Policy` 实现。
- `experiments/external_model_adapter.py`：无网络假 transport 教学实验和稳定 JSON 输出。
- `tests/test_model_adapters.py`：请求、响应、校验与秘密保护测试。
- `tests/test_model_policy.py`：领域编码与完整 Loop/Artifact 集成测试。
- `tests/test_external_model_adapter.py`：教学实验的无网络、稳定输出测试。
- `docs/external-model-adapter.md`、`docs/experiments.md`、两份 README、进度文档：学习说明与导航。

## Task 1: Build the explicit HTTP adapter

**Files:**
- Create: `tests/test_model_adapters.py`
- Create: `loop_engineering/model_adapters.py`

**Interfaces:**
- Produces: `ModelAdapterError`, `HttpResponse`, `HttpTransport`, `UrllibHttpTransport`, `HttpModelAdapter.complete(input_payload) -> Decision`.
- Consumed later by: `ModelPolicy` and the no-network experiment.

- [ ] **Step 1: Write failing adapter contract tests**

Create `tests/test_model_adapters.py`:

```python
import pytest

from loop_engineering.model_adapters import (
    HttpModelAdapter,
    HttpResponse,
    ModelAdapterError,
)


class FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        self.calls.append(
            {
                "endpoint": endpoint,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response


def test_adapter_posts_explicit_json_and_optional_authorization() -> None:
    transport = FakeTransport(
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": 2}}')
    )
    adapter = HttpModelAdapter(
        "https://models.example.test/decide",
        "study-model",
        "secret-value",
        transport,
        timeout_seconds=3.0,
    )

    decision = adapter.complete({"state": {"goal": 2.0}})

    assert decision.name == "increment"
    assert decision.parameters == {"amount": 2.0}
    assert transport.calls == [{
        "endpoint": "https://models.example.test/decide",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret-value",
        },
        "payload": {"model": "study-model", "input": {"state": {"goal": 2.0}}},
        "timeout_seconds": 3.0,
    }]


def test_adapter_rejects_insecure_endpoint_and_invalid_model_or_timeout() -> None:
    with pytest.raises(ModelAdapterError, match="HTTPS"):
        HttpModelAdapter("http://models.example.test", "model", "")
    with pytest.raises(ModelAdapterError, match="model"):
        HttpModelAdapter("https://models.example.test", "", "")
    with pytest.raises(ModelAdapterError, match="timeout"):
        HttpModelAdapter("https://models.example.test", "model", "", timeout_seconds=0)


@pytest.mark.parametrize(
    "response",
    [
        HttpResponse(500, "service failed"),
        HttpResponse(200, "not-json"),
        HttpResponse(200, '{"name": "", "parameters": {}}'),
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": true}}'),
    ],
)
def test_adapter_rejects_invalid_responses_without_exposing_key(response) -> None:
    adapter = HttpModelAdapter(
        "https://models.example.test",
        "model",
        "secret-value",
        FakeTransport(response),
    )

    with pytest.raises(ModelAdapterError) as error:
        adapter.complete({})

    assert "secret-value" not in str(error.value)
```

- [ ] **Step 2: Run adapter tests to verify RED**

Run: `python -m pytest tests/test_model_adapters.py -q`

Expected: collection fails because `loop_engineering.model_adapters` does not exist.

- [ ] **Step 3: Implement the adapter module**

Create `loop_engineering/model_adapters.py` with these public definitions:

```python
class ModelAdapterError(ValueError):
    """Raised when a model endpoint or its response violates the adapter contract."""


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: str


class HttpTransport(Protocol):
    def post_json(
        self,
        endpoint: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> HttpResponse: ...
```

Implement `UrllibHttpTransport.post_json` with `json.dumps(payload).encode("utf-8")`, `urllib.request.Request(..., method="POST")`, `urlopen(..., timeout=timeout_seconds)`, and an `HttpResponse` for both normal responses and `HTTPError`.

Implement `HttpModelAdapter.__init__` to reject non-HTTPS endpoints, empty/whitespace models, and non-positive timeout; store either the injected transport or `UrllibHttpTransport()`. Implement `complete` to call the transport with:

```python
headers = {"Content-Type": "application/json"}
if self.api_key:
    headers["Authorization"] = f"Bearer {self.api_key}"
payload = {"model": self.model, "input": input_payload}
```

For 2xx responses, parse JSON, require non-empty string `name`, require dictionary `parameters`, require string keys and finite numeric non-boolean values, then return `Decision(name=name, parameters={key: float(value) for ...})`. Every failure raises `ModelAdapterError` with a message that omits API Key, endpoint and response body.

- [ ] **Step 4: Run adapter tests to verify GREEN**

Run: `python -m pytest tests/test_model_adapters.py -q`

Expected: all adapter contract tests pass.

- [ ] **Step 5: Commit**

```powershell
git add loop_engineering/model_adapters.py tests/test_model_adapters.py
git commit -m "feat: add external model adapter"
```

## Task 2: Connect the adapter through a Policy and verify Artifact safety

**Files:**
- Create: `tests/test_model_policy.py`
- Create: `loop_engineering/model_policy.py`

**Interfaces:**
- Consumes: `HttpModelAdapter.complete(dict[str, object]) -> Decision`, `LoopState`, `Feedback`, `LoopEvent`.
- Produces: `ModelPolicy(adapter: HttpModelAdapter)`, compatible with `LoopRunner`.

- [ ] **Step 1: Write failing policy and loop integration tests**

Create `tests/test_model_policy.py`:

```python
from loop_engineering.actions import NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.model_adapters import HttpModelAdapter, HttpResponse
from loop_engineering.model_policy import ModelPolicy
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


class FakeTransport:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        self.payloads.append(payload)
        return HttpResponse(200, '{"name": "increment", "parameters": {"amount": 2}}')


def test_model_policy_encodes_state_feedback_and_recent_events() -> None:
    transport = FakeTransport()
    policy = ModelPolicy(HttpModelAdapter("https://models.example.test", "model", "", transport))
    state = LoopState(step=1, value=2.0, goal=4.0)
    feedback = Feedback(score=0.5, message="continue", signals={"error": 2.0})
    recent = [LoopEvent(step=0, phase="OBSERVE", payload={"goal": 4.0})]

    decision = policy.decide(state, feedback, recent)

    assert decision.parameters == {"amount": 2.0}
    assert transport.payloads == [{
        "model": "model",
        "input": {
            "state": {"step": 1, "value": 2.0, "goal": 4.0, "status": "RUNNING", "metadata": {}},
            "feedback": {"score": 0.5, "message": "continue", "signals": {"error": 2.0}},
            "recent_events": [{"step": 0, "phase": "OBSERVE", "payload": {"goal": 4.0}}],
        },
    }]


def test_model_policy_runs_and_persists_without_api_key(tmp_path) -> None:
    transport = FakeTransport()
    policy = ModelPolicy(HttpModelAdapter("https://models.example.test", "model", "secret-value", transport))
    trace = LoopRunner(
        policy, NumericAction(), GoalEvaluator(0.0), [SuccessReached(), MaxSteps(2)]
    ).run(LoopState(step=0, value=0.0, goal=2.0))
    artifact_path = save_run_artifact(tmp_path / "run.json", trace)

    payload = artifact_path.read_text(encoding="utf-8")
    assert trace.final_state is not None and trace.final_state.status == "SUCCEEDED"
    assert "secret-value" not in payload
    assert trace.events[1].payload == {"name": "increment", "parameters": {"amount": 2.0}}
```

- [ ] **Step 2: Run policy tests to verify RED**

Run: `python -m pytest tests/test_model_policy.py -q`

Expected: collection fails because `loop_engineering.model_policy` does not exist.

- [ ] **Step 3: Implement ModelPolicy**

Create `loop_engineering/model_policy.py`:

```python
from dataclasses import asdict
from typing import Sequence

from .model_adapters import HttpModelAdapter
from .models import Feedback, LoopEvent, LoopState
from .policies import Decision, Policy


class ModelPolicy(Policy):
    def __init__(self, adapter: HttpModelAdapter) -> None:
        self.adapter = adapter

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        return self.adapter.complete(
            {
                "state": asdict(state),
                "feedback": asdict(feedback),
                "recent_events": [asdict(event) for event in recent_events or ()],
            }
        )
```

- [ ] **Step 4: Run policy tests to verify GREEN**

Run: `python -m pytest tests/test_model_policy.py -q`

Expected: both policy tests pass and the saved Artifact contains no API Key.

- [ ] **Step 5: Commit**

```powershell
git add loop_engineering/model_policy.py tests/test_model_policy.py
git commit -m "feat: add model policy integration"
```

## Task 3: Add a no-network learning experiment and documentation

**Files:**
- Create: `experiments/external_model_adapter.py`
- Create: `tests/test_external_model_adapter.py`
- Create: `docs/external-model-adapter.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: `HttpModelAdapter`, `HttpResponse`, `ModelPolicy`, existing `LoopRunner`, `save_run_artifact`.
- Produces: `run_external_model_adapter_demo(output_dir: str | Path = ".loop/runs/external-model-adapter") -> dict[str, object]`.

- [ ] **Step 1: Write the failing no-network experiment test**

Create `tests/test_external_model_adapter.py`:

```python
import json
from pathlib import Path

from experiments.external_model_adapter import run_external_model_adapter_demo
from loop_engineering.artifacts import load_run_artifact


def test_external_model_adapter_demo_is_replayable_and_does_not_need_network(tmp_path: Path) -> None:
    result = run_external_model_adapter_demo(tmp_path)

    assert result["status"] == "SUCCEEDED"
    assert result["decision_count"] == 1
    artifact_path = Path(result["artifact_path"])
    trace, metrics = load_run_artifact(artifact_path)
    assert metrics.success is True
    assert trace.events[1].payload == {"name": "increment", "parameters": {"amount": 2.0}}
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == result
```

- [ ] **Step 2: Run experiment test to verify RED**

Run: `python -m pytest tests/test_external_model_adapter.py -q`

Expected: collection fails because `experiments.external_model_adapter` does not exist.

- [ ] **Step 3: Implement the fake-transport experiment**

Create `experiments/external_model_adapter.py` with a local `DemoTransport` whose `post_json` always returns `HttpResponse(200, '{"name": "increment", "parameters": {"amount": 2.0}}')`. Construct an `HttpModelAdapter` with `https://example.invalid/decide`, model `"demo-model"`, empty API Key and that transport. Run `ModelPolicy` with `NumericAction`, `GoalEvaluator(0.0)`, `SuccessReached()`, and `MaxSteps(2)` from an initial goal of 2.0. Save `artifact.json` and UTF-8 `report.json` containing `artifact_path`, `status`, `decision_count`, and `network_calls` equal to the fake transport call count. Add `main()` that prints the returned report with `ensure_ascii=False`.

- [ ] **Step 4: Run the experiment test and direct script**

Run:

```powershell
python -m pytest tests/test_external_model_adapter.py -q
python experiments/external_model_adapter.py
```

Expected: test passes; direct script outputs a successful report while making no real network request.

- [ ] **Step 5: Document the adapter and navigation**

Create `docs/external-model-adapter.md` covering: explicit configuration only, HTTPS restriction, fixed request/response JSON schemas, fake transport for tests, API Key exclusion from trace/Artifact, and the distinction between the no-network demo and a user-provided real endpoint.

Add `python experiments/external_model_adapter.py` to `docs/experiments.md`. Add learning-path links in both README files. Append a progress entry that records the adapter, `ModelPolicy`, no-network demo and the exact final pytest count obtained in Step 6.

- [ ] **Step 6: Run complete verification and commit**

Run:

```powershell
python -m pytest -q
git diff --check
```

Expected: all tests pass and the whitespace check has no output.

Commit:

```powershell
git add experiments/external_model_adapter.py tests/test_external_model_adapter.py docs/external-model-adapter.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: add external model adapter guide"
```

