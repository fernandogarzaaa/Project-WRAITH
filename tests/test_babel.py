"""Real tests for the Babel LLM-to-LLM compression protocol."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from babel.protocol import BabelParser


def test_roundtrip_serialize_parse():
    msg = BabelParser.serialize(
        "ORC", "A1F4", 95, {"target": "agent_3", "action": "terminate", "reason": "idle"}
    )
    parsed = BabelParser.parse(msg)
    assert parsed is not None
    assert parsed["domain"] == "ORC"
    assert parsed["intent"] == "A1F4"
    assert parsed["confidence"] == 95
    assert parsed["payload"] == {"target": "agent_3", "action": "terminate", "reason": "idle"}


def test_parse_documented_example():
    parsed = BabelParser.parse("%%ORC:1A4F:98%%{{route=agent_beta;task=deploy;timeout=30}}")
    assert parsed is not None
    assert parsed["domain"] == "ORC"
    assert parsed["confidence"] == 98
    assert parsed["payload"]["timeout"] == "30"


def test_malformed_inputs_return_none_not_crash():
    assert BabelParser.parse("hello world") is None
    assert BabelParser.parse("%%ORC:A1F4:95%%{{broken") is None
    assert BabelParser.parse("") is None


def test_serialize_confidence_zero_padded():
    msg = BabelParser.serialize("DBG", "00FF", 5, {})
    assert ":05%%" in msg
