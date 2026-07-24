# 外部 HTTP 模型适配层

本模块展示如何让外部模型在不改变核心 Loop 边界的情况下生成 `Decision`。默认项目不读取环境变量，也不访问网络；只有调用方显式创建适配器并调用它时，才可能发送请求。

## 显式配置

```python
from loop_engineering.model_adapters import HttpModelAdapter
from loop_engineering.model_policy import ModelPolicy

adapter = HttpModelAdapter(
    endpoint="https://your-model.example/decide",
    model="your-model",
    api_key="provided-by-the-caller",
)
policy = ModelPolicy(adapter)
```

端点必须使用 HTTPS。API Key 仅在非空时作为 `Authorization: Bearer ...` 请求头发送；它不会写入 Trace、Artifact、stdout 或适配器错误消息。

## JSON 契约

每次调用发送：

```json
{
  "model": "your-model",
  "input": {
    "state": {},
    "feedback": {},
    "recent_events": []
  }
}
```

模型必须返回：

```json
{
  "name": "increment",
  "parameters": {
    "amount": 1.0
  }
}
```

`name` 必须是非空字符串；`parameters` 的键必须为字符串，值必须是有限数值。非 2xx 响应、无效 JSON 和不符合结构的返回会触发 `ModelAdapterError`，不会被静默转换为决策。

## 无网络教学示例

```powershell
python experiments/external_model_adapter.py
```

示例注入本地假 transport，而不是访问 `example.invalid`。它生成可回放 Artifact 和 `report.json`，用于演示外部模型如何通过 `ModelPolicy` 进入既有的 `Policy -> Decision -> Action -> Trace` 闭环。

## 使用边界

该适配器是学习用的最小 HTTP JSON 边界，不提供厂商 SDK、密钥管理、自动重试、流式输出或工具执行。真实服务的认证、配额、重试策略和安全审批应由调用方在该边界之外明确处理。

