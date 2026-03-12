import json
import re
from pathlib import Path

from comedy_duo.models import EventTier, SessionEvent

CORRECTION_PATTERNS = re.compile(
    r"(no[,.]?\s+(that's|thats)\s+wrong|don't do|instead\s+do|not\s+that|wrong\s+approach|"
    r"stop|undo\s+that|revert|that's\s+not\s+what\s+I)",
    re.IGNORECASE,
)

ERROR_PATTERNS = re.compile(
    r"(FAILED|Error:|error:|Traceback|exception|exit\s+code:\s+[1-9]|"
    r"ModuleNotFoundError|ImportError|SyntaxError|TypeError|ValueError|"
    r"command\s+not\s+found|Permission\s+denied)",
    re.IGNORECASE,
)

APOLOGY_PATTERNS = re.compile(
    r"(I\s+apologize|I'm\s+sorry|my\s+mistake|let\s+me\s+fix\s+that|"
    r"I\s+was\s+wrong|that\s+was\s+incorrect)",
    re.IGNORECASE,
)


def classify_jsonl_line(line: str) -> SessionEvent | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = data.get("type")
    message = data.get("message")

    if msg_type in ("progress", "file-history-snapshot", "system"):
        return None

    if not message:
        return None

    if msg_type == "user":
        content = message.get("content", "")
        if isinstance(content, str) and CORRECTION_PATTERNS.search(content):
            return SessionEvent(
                tier=EventTier.HOT,
                event_type="user_correction",
                summary=content[:200],
                raw_data=data,
            )
        return None

    if msg_type == "assistant":
        content = message.get("content", [])
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        for block in content:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type", "")

            if block_type == "tool_result":
                result_text = block.get("content", "")
                if isinstance(result_text, str) and ERROR_PATTERNS.search(result_text):
                    # Distinguish test failures from generic errors
                    if re.search(r"\bFAILED\b", result_text):
                        event_type = "test_failure"
                    else:
                        event_type = "error"
                    return SessionEvent(
                        tier=EventTier.HOT,
                        event_type=event_type,
                        summary=result_text[:200],
                        raw_data=data,
                    )

            if block_type == "text":
                text = block.get("text", "")
                if APOLOGY_PATTERNS.search(text):
                    return SessionEvent(
                        tier=EventTier.HOT,
                        event_type="apology",
                        summary=text[:200],
                        raw_data=data,
                    )

            if block_type == "tool_use":
                tool_name = block.get("name", "")

                if tool_name == "Write":
                    file_path = block.get("input", {}).get("file_path", "")
                    return SessionEvent(
                        tier=EventTier.WARM,
                        event_type="new_file",
                        summary=f"Created {file_path}",
                        raw_data=data,
                    )

                if tool_name == "Bash":
                    cmd = block.get("input", {}).get("command", "")
                    if any(kw in cmd for kw in ("pip install", "npm install", "brew install")):
                        return SessionEvent(
                            tier=EventTier.WARM,
                            event_type="dependency_install",
                            summary=f"Installing: {cmd[:100]}",
                            raw_data=data,
                        )
                    if "git commit" in cmd:
                        return SessionEvent(
                            tier=EventTier.WARM,
                            event_type="commit",
                            summary=f"Committing: {cmd[:100]}",
                            raw_data=data,
                        )

                if tool_name in ("Read", "Edit", "Glob", "Grep"):
                    return None

    return None


def find_latest_session(sessions_dir: Path) -> Path | None:
    jsonl_files = list(sessions_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)
