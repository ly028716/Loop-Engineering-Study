"""循环运行时共享的领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, ClassVar


@dataclass(frozen=True)
class LoopState:
    """某一轮循环中的状态快照。"""

    step: int
    value: float
    goal: float
    status: str = "RUNNING"
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_value(self, value: float, **metadata: Any) -> "LoopState":
        """返回值已更新且步数递增的新状态，而不修改当前状态。"""

        return replace(
            self,
            step=self.step + 1,
            value=value,
            metadata={**self.metadata, **metadata},
        )


@dataclass
class Feedback:
    """评估阶段提供给下一轮策略的反馈。"""

    score: float
    message: str
    signals: dict[str, Any]

    @classmethod
    def empty(cls) -> "Feedback":
        """创建没有评估信号的中性反馈。"""

        return cls(score=0.0, message="", signals={})


@dataclass
class LoopEvent:
    """一条可持久化的循环阶段事件。"""

    VALID_PHASES: ClassVar[frozenset[str]] = frozenset(
        {"OBSERVE", "DECIDE", "ACT", "EVALUATE", "FEEDBACK", "STOP"}
    )

    step: int
    phase: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.phase not in self.VALID_PHASES:
            raise ValueError(f"Unsupported loop phase: {self.phase}")


@dataclass
class LoopTrace:
    """一次循环运行累积的事件及其最终状态。"""

    events: list[LoopEvent] = field(default_factory=list)
    final_state: LoopState | None = None

    def append(self, phase: str, step: int, payload: dict[str, Any]) -> None:
        """将经过校验的阶段事件追加到轨迹。"""

        self.events.append(LoopEvent(step=step, phase=phase, payload=payload))
