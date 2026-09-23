from agora3.chat_activity import ChatActivity


def test_snapshot_survives_missed_polls_and_keeps_message_boundaries():
    activity = ChatActivity()
    for _ in range(350):
        activity.observe({"type": "text.delta", "id": "progress", "text": "a"})
    activity.observe({"type": "text.completed", "id": "progress", "text": "a" * 350,
                      "phase": "commentary"})
    activity.observe({"type": "text.delta", "id": "final", "text": "Done"})
    activity.observe({"type": "text.completed", "id": "final", "text": "Done.",
                      "phase": "final_answer"})
    snapshot = activity.snapshot()
    assert snapshot["messages"][0]["text"] == "a" * 350
    assert snapshot["messages"][1]["text"] == "Done."
    assert snapshot["messages"][1]["phase"] == "final_answer"
    snapshot["messages"][0]["text"] = "edited by consumer"
    assert activity.snapshot()["messages"][0]["text"] == "a" * 350


def test_tool_progress_contains_no_command_or_result_and_is_bounded():
    activity = ChatActivity()
    activity.observe({"type":"tool.started", "name":"guest.execute", "arguments":{"command":"private"}})
    activity.observe({"type":"tool.completed", "name":"guest.execute", "result":{"stdout":"private"}})
    assert "private" not in str(activity.snapshot())
    assert not activity.snapshot()["tool"]["running"]
    for i in range(120):
        activity.observe({"type":"text.delta", "id":str(i), "text":"x" * 20_000})
    snapshot = activity.snapshot()
    assert len(snapshot["messages"]) <= 100
    assert sum(len(m["text"]) for m in snapshot["messages"]) <= 1_000_000
