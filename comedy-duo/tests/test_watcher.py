import json
import time
import pytest
from comedy_duo.watcher import classify_jsonl_line, find_latest_session
from comedy_duo.models import EventTier


class TestClassifyLine:
    def test_test_failure_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_result", "content": "FAILED tests/test_auth.py - AssertionError"}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT
        assert "fail" in event.event_type.lower()

    def test_apology_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "I apologize for the confusion."}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_new_file_is_warm(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "src/new.py", "content": "x"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.WARM

    def test_file_read_is_cold(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "src/main.py"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is None

    def test_progress_line_is_cold(self):
        line = json.dumps({"type": "progress", "message": None})
        event = classify_jsonl_line(line)
        assert event is None

    def test_user_correction_is_hot(self):
        line = json.dumps({
            "type": "user",
            "message": {"role": "user", "content": "no that's wrong, do it this way instead"},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_bash_error_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_result", "content": "Error: command not found\nexit code: 127"}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_edit_is_cold(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "x.py", "old_string": "a", "new_string": "b"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is None


class TestFindLatestSession:
    def test_finds_most_recent_jsonl(self, tmp_path):
        old = tmp_path / "old.jsonl"
        old.write_text("{}\n")
        time.sleep(0.05)
        new = tmp_path / "new.jsonl"
        new.write_text("{}\n")
        result = find_latest_session(tmp_path)
        assert result == new

    def test_returns_none_if_empty(self, tmp_path):
        result = find_latest_session(tmp_path)
        assert result is None
