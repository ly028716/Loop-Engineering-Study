# 运行生命周期与 Memory 契约设计

## 目标

确保每次 `LoopRunner.run()` 都拥有独立、可解释的 WorkingMemory 上下文，使一个 Artifact 的 Trace 足以解释该次运行中传给策略的历史事件。

## 问题

当前 `LoopRunner` 在构造时创建或接收一个 `WorkingMemory`，但重复调用同一 runner 的 `run()` 不会清空它。第二次运行的首次决策可能读取第一次运行事件，而第二次 Trace/Artifact 不包含这些事件。因此 Artifact 不能完整解释决策输入。

## 契约

WorkingMemory 是单次 run 内的有界、有序事件窗口，不是跨运行持久化记忆。

- `WorkingMemory.clear() -> None` 清空已存事件，保留 `capacity`；
- `LoopRunner.run(initial_state)` 在创建新 `LoopTrace` 前调用 `self.memory.clear()`；
- 首次决策只会看到本次运行刚记录的 `OBSERVE` 事件；
- 后续决策继续看到本次运行内、受容量限制的历史事件；
- 显式传入的 memory 对象保持同一对象身份：一次 run 结束后，它包含该次运行的事件；下一次 run 开始时才被清空；
- 不改变 Artifact 格式、CLI、实验接口或 Policy 的 `decide` 签名。

## 实现边界

在 `loop_engineering.memory.WorkingMemory` 增加：

```python
def clear(self) -> None:
    """Forget all events while retaining the configured capacity."""
```

实现仅调用底层 `deque.clear()`。在 `LoopRunner.run()` 的开头、任何 `OBSERVE` 事件写入前调用它。该行为只影响跨调用 runner 的旧事件；同一次 run 内的 `_record_event()` 和 `_decide()` 逻辑保持不变。

## 测试

新增/更新测试覆盖：

1. `clear()` 清除窗口、保留 capacity，且随后仍可添加事件；
2. 同一 runner 连续运行两次时，第二次第一次决策仅接收当前运行的 `OBSERVE`；
3. 第二次 run 完成后，显式 memory 的内容等于第二次 Trace 事件；
4. 既有单次运行内的 memory 策略上下文测试继续通过。

## 文档

更新 `docs/memory-capacity.md` 与 `docs/architecture.md`，明确 WorkingMemory 的单次运行范围和 Artifact 自包含语义；进度记录最终测试数量。

## 验收标准

- 同一 runner 的重复运行不会向 policy 泄漏旧 run 事件；
- 每个保存的 Artifact 都可独立解释其决策所见事件；
- 单次运行内的 memory-aware 行为不变；
- 完整 pytest 通过。

