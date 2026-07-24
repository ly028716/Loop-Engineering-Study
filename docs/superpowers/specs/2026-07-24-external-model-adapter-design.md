# 外部模型适配层设计

## 目标

在不改变确定性基线与默认零网络行为的前提下，为 Loop Engineering 学习项目加入一个可测试的通用 HTTP 模型适配层。外部模型通过既有 `Policy` 边界产生 `Decision`，从而进入现有 Action、Trace、Artifact 与评估闭环。

## 范围

第一阶段仅覆盖通用 HTTP JSON 模型调用：

- 显式构造配置：`endpoint`、`model`、`api_key`、可选 `timeout_seconds`；
- 标准库 HTTP transport 抽象与可替换假 transport；
- 严格 JSON 请求/响应契约；
- 将合法模型输出解析为既有 `Decision`；
- 一个不联网的教学实验与文档。

不包含厂商 SDK、环境变量读取、真实密钥示例、自动重试、流式响应、工具执行、批量调用或 Artifact 格式变更。

## 架构

```text
LoopState + Feedback + recent events
        ↓
ModelPolicy.decide()
        ↓
HttpModelAdapter.complete(request)
        ↓
HttpTransport.post_json()
        ↓
external HTTPS JSON endpoint
        ↓
{"name": "...", "parameters": {...}}
        ↓
Decision → existing Action → Trace / Artifact
```

### `loop_engineering/model_adapters.py`

提供：

- `ModelAdapterError(ValueError)`：表示端点校验、HTTP 响应、JSON 解析与模型输出结构错误；
- `HttpResponse(status_code: int, body: str)`：不可变 transport 返回值；
- `HttpTransport` 协议：`post_json(endpoint: str, headers: dict[str, str], payload: dict[str, object], timeout_seconds: float) -> HttpResponse`；
- `UrllibHttpTransport`：唯一真实网络实现，使用 `urllib.request`；
- `HttpModelAdapter(endpoint: str, model: str, api_key: str, transport: HttpTransport | None = None, timeout_seconds: float = 10.0)`；
- `complete(input_payload: dict[str, object]) -> Decision`：发送固定请求并将响应严格解析为决策。

构造器只接受 `https://` endpoint，`model` 不能为空，`timeout_seconds` 必须大于零。它不读取环境变量。请求体固定为：

```json
{
  "model": "configured-model",
  "input": {
    "state": {},
    "feedback": {},
    "recent_events": []
  }
}
```

请求始终包含 `Content-Type: application/json`。仅当 `api_key` 非空时附加 `Authorization: Bearer <api_key>`。

### `loop_engineering/model_policy.py`

提供 `ModelPolicy(adapter: HttpModelAdapter)`，实现既有 `Policy.decide(state, feedback, recent_events=None) -> Decision`。它使用 `dataclasses.asdict()` 编码 `state`、`feedback` 与事件列表，在没有近期事件时传递空列表。它不记录密钥，也不直接处理网络细节。

## 响应与错误契约

成功的 HTTP JSON 响应必须是对象：

```json
{
  "name": "increment",
  "parameters": {
    "amount": 1.0
  }
}
```

`name` 必须是非空字符串；`parameters` 必须是对象，键为字符串、值为有限数值（拒绝布尔值）。适配器将数值规范为 `float`，然后创建 `Decision`。

以下场景抛出 `ModelAdapterError`：非 2xx 响应、无效 JSON、JSON 顶层不是对象、缺少字段、字段类型错误或非有限参数值。异常消息不得包含 API Key 或完整 Authorization 值。默认情况下没有模型实例，因此项目不会发起任何外部请求。

## 可观测性与安全边界

`LoopRunner`、`Action`、`Evaluator`、Artifact 格式与 CLI 的默认 `run` 行为保持不变。模型选择出的 `Decision` 会沿用现有 DECIDE Trace 事件，只记录名称和数值参数；端点、请求正文与凭据不进入 Trace、Artifact、stdout 或异常文本。

`UrllibHttpTransport` 仅在调用方显式构造并调用 `HttpModelAdapter` 时使用。教学实验只注入假 transport，确保 CI 和学习示例不会访问网络。

## 验证与文档

新增测试覆盖：

1. HTTPS 构造校验、空模型与非法超时；
2. 请求的 endpoint、JSON body、Content-Type 与可选 Authorization；
3. 非 2xx、无效 JSON 和错误响应结构的安全失败；
4. 合法 JSON 响应转换为 `Decision`；
5. `ModelPolicy` 对状态、反馈和最近事件的编码；
6. `ModelPolicy` 注入现有 `LoopRunner` 后产生可保存、可加载且不含 API Key 的 Artifact；
7. 教学实验不联网且输出稳定 JSON。

新增学习文档解释显式配置、响应契约、假 transport 和生产使用边界；README 与实验导航链接到该文档。

## 验收标准

- 真实模型调用可通过用户显式提供的 HTTPS endpoint、模型名与 API Key 完成；
- 无真实配置时项目仍保持默认确定性、无网络依赖；
- 不会将 API Key 写入 Trace、Artifact 或错误消息；
- 模型输出严格转换为既有 `Decision`，错误输出明确失败；
- 全量 pytest 通过。

