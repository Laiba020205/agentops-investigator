
from app.tracing.collector import TraceCollector


def test_collector_records_events_in_order():
    collector = TraceCollector()
    run_id = collector.start_run()

    collector.record(
        run_id=run_id,
        event_type="agent_start",
        name="test_agent",
    )

    collector.record(
        run_id=run_id,
        event_type="error",
        name="test_tool",
        output_data={"error": "Missing order_id"},
        status="failure",
    )

    events = collector.get_events(run_id)

    assert len(events) == 2
    assert events[0].sequence == 1
    assert events[1].sequence == 2
    assert events[1].status == "failure"
    assert events[1].output_data["error"] == "Missing order_id"
