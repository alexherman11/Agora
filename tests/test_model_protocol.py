from types import SimpleNamespace as NS

from agora3.model_protocol import ThreadEnvelope, payload


def test_unknown_runtime_envelopes_preserve_forward_compatible_payloads():
    event = NS(
        payload=NS(params={"threadId": "t", "item": {"type": "subAgentActivity", "id": "x"}})
    )
    assert payload(event).thread_id == "t"
    assert payload(event).item.type == "subAgentActivity"
    assert (
        ThreadEnvelope.model_validate(
            {"thread": {"id": "t", "turns": [{"unknown": "future"}]}, "model": "m"}
        ).thread.id
        == "t"
    )


def test_unknown_completed_turn_preserves_failure_reason():
    event = NS(
        payload=NS(params={"turn": {"status": "failed", "error": {"message": "Failure retained"}}})
    )
    assert payload(event).turn.error.message == "Failure retained"
