"""JSON Lines 格式的循环事件持久化。"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from loop_engineering.models import LoopEvent


class JsonlTraceStore:
    """将每个循环事件写入一行 UTF-8 JSON 的简单存储。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: LoopEvent) -> None:
        """追加一个事件，并在需要时创建其父目录。"""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as trace_file:
            json.dump(asdict(event), trace_file, ensure_ascii=False)
            trace_file.write("\n")

    def load(self) -> list[LoopEvent]:
        """从现有 JSONL 文件恢复事件；尚未写入时返回空列表。"""

        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as trace_file:
            return [LoopEvent(**json.loads(line)) for line in trace_file if line.strip()]
