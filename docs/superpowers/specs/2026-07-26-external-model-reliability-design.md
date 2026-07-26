# 外部模型生产化可靠性控制设计

## 目标

为现有 `HttpModelAdapter` 增加可配置、可测试的调用可靠性控制：对可恢复失败执行确定性重试和指数退避；连续失败时熔断；在重试耗尽或熔断拒绝时显式终止本次模型调用。

本阶段只处理传输可靠性，不改变 Loop、Trace、Artifact 或 `ModelPolicy` 的既有契约。

## 范围

支持：

- 网络异常、超时、HTTP `429` 和 `5xx` 的有限重试；
- 固定公式的指数退避；
- 适配器实例内的 `closed`、`open`、`half-open` 熔断状态机；
- 无敏感信息的可靠性快照；
- 无网络的教学实验和确定性单元测试。

不支持：

- 随机抖动、跨进程共享熔断状态或分布式协调；
- 自动回退到其他策略、伪造 `Decision` 或静默吞掉错误；
- 费用预算、限流、密钥管理、审计存储、厂商 SDK 与环境变量读取；
- 请求体、响应体、API Key 或模型输出的持久化。

## 架构

可靠性控制位于 `HttpModelAdapter` 内部，保留 `ModelPolicy -> complete() -> Decision` 的调用链。调用方可以显式传入 `ReliabilityPolicy`；未传入时使用安全且可复现的默认值。

`HttpTransport` 接口保持不变。`UrllibHttpTransport` 继续把 HTTP 响应转换为 `HttpResponse`，并让网络异常与超时向上传播，由适配器统一分类。

### 配置与默认值

新增不可变的 `ReliabilityPolicy`：

```python
@dataclass(frozen=True)
class ReliabilityPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.1
    failure_threshold: int = 3
    cooldown_seconds: float = 30.0
```

- `max_attempts` 是包括首次请求在内的总尝试次数，必须大于 0。
- `base_delay_seconds` 与 `cooldown_seconds` 必须不小于 0。
- `failure_threshold` 必须大于 0。
- 第 `retry_index` 次重试前的等待时间为 `base_delay_seconds × 2^retry_index`，其中第一次重试的 `retry_index` 为 0。
- 不使用随机抖动，确保测试与教学输出稳定。

`HttpModelAdapter` 新增可选构造参数：

```python
HttpModelAdapter(
    endpoint,
    model,
    api_key,
    transport=None,
    timeout_seconds=10.0,
    reliability_policy=None,
    clock=time.monotonic,
    sleeper=time.sleep,
)
```

`clock` 和 `sleeper` 仅用于测试和教学中的时间控制；生产默认使用标准库实现。

## 失败分类与重试

可恢复失败包括：

- `URLError`、套接字超时与其他传输层 `OSError`；
- HTTP `429`；
- HTTP `500` 至 `599`。

适配器对每次可恢复失败更新连续失败数。若仍有剩余尝试次数，调用 `sleeper()` 后重试；重试耗尽时抛出 `ModelAdapterError`，错误消息只包含失败类别、状态码（如有）和已尝试次数，不包含 API Key、请求体或响应体。

以下情况不可恢复且不重试：HTTP `400` 至 `499`（`429` 除外）、无效 JSON、响应不是对象、缺少 `name` 或 `parameters`、以及参数不符合已有有限数值契约。

## 熔断状态机

熔断状态按 `HttpModelAdapter` 实例保存：

```text
closed --连续可恢复失败达到阈值--> open
open --冷却到期且第一个调用到达--> half-open
half-open --探测成功--> closed
half-open --可恢复失败或重试耗尽--> open
```

- `closed`：允许调用。成功调用将连续失败数重置为 0。
- `open`：在 `clock() < opened_at + cooldown_seconds` 时，`complete()` 立即抛出 `ModelAdapterError`，且绝不调用 transport。
- `half-open`：冷却到期后的首个调用是唯一探测调用。探测成功后关闭熔断器并清零失败数；探测失败后重新打开并更新 `opened_at`。
- 为保证单线程学习运行时的行为确定，半开状态不提供并发探测协调；并发生产部署属于后续独立课题。

新增只读 `reliability_snapshot() -> dict[str, object]`，返回：

```python
{
    "state": "closed",
    "consecutive_failures": 0,
    "next_probe_at": None,
}
```

快照不得包含端点、模型名、API Key、请求内容或响应内容。

## 错误与可观察性

当重试耗尽、熔断器仍处于打开状态或半开探测失败时，适配器抛出 `ModelAdapterError`。`ModelPolicy` 不捕获该异常，因此 Loop 不会伪造决策或继续执行不可信动作。

本阶段不修改 `LoopRunner` 的 Trace 事件，也不把可靠性快照、响应正文或重试细节写入 Artifact。教学实验的独立 `report.json` 可以记录场景名、尝试次数、sleep 序列、最终结果和脱敏快照。

## 教学实验

新增 `experiments/external_model_reliability.py`，通过顺序化 fake transport 演示：

1. 一次 HTTP `429` 后重试成功；
2. 连续可恢复失败触发熔断，打开期间不再调用 transport；
3. 冷却完成后的半开探测成功并关闭熔断器。

实验不访问网络，不使用真实 API Key，并仅向调用方指定的输出目录写入 `report.json` 与可回放 Artifact。

## 验证与验收

测试必须覆盖：

1. 可恢复与不可恢复失败的分类；
2. 固定指数退避序列与重试次数；
3. 重试耗尽时的明确错误；
4. `closed -> open -> half-open -> closed` 状态转移；
5. 熔断打开期间 transport 调用次数不增加；
6. 半开失败重新打开；
7. 可靠性快照不泄露敏感信息；
8. `ModelPolicy` 仍能从成功调用得到原有 `Decision`；
9. 无网络实验报告稳定、Artifact 可回放；
10. 全量 pytest 通过。

验收时应证明：只有规定失败会重试；熔断打开时不发出网络调用；每个错误路径都显式失败；默认项目运行不访问网络。
