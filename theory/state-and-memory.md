# State and Memory

`LoopState` 是当前轮的不可变快照。动作通过 `with_value()` 产生下一轮状态，
不会修改先前状态，因此 trace 可以重放和比较。`LoopTrace` 保存整个运行的
事件序列，而 `WorkingMemory` 保留一个有容量上限的近期事件窗口；支持该参数的
策略可把这个窗口纳入决策。

状态回答“系统现在在哪里”，记忆回答“最近发生了什么”。反馈则是经过评估后专门
传递给策略的一小段摘要。分开这三者可避免将历史、当前数据和控制信号混为一谈。

[retry_loop](../experiments/retry_loop.py) 主要通过反馈恢复，但它也会由 runner
记录完整的事件历史。可将它与 [basic_loop](../experiments/basic_loop.py) 对照，
观察同一状态模型在不同控制信息下的行为。
