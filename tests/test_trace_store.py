def test_trace_store_round_trips_jsonl_and_creates_parent_directory(tmp_path) -> None:
    from loop_engineering.models import LoopEvent
    from loop_engineering.trace_store import JsonlTraceStore

    path = tmp_path / "nested" / "trace.jsonl"
    store = JsonlTraceStore(path)
    events = [
        LoopEvent(step=1, phase="OBSERVE", payload={"value": 2.0}),
        LoopEvent(step=1, phase="FEEDBACK", payload={"message": "继续"}),
    ]

    for event in events:
        store.append(event)

    assert path.is_file()
    assert store.load() == events
    assert "继续" in path.read_text(encoding="utf-8")
