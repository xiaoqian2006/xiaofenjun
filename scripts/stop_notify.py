#!/usr/bin/env python3
"""Send a macOS notification when a Codex turn finishes."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


PLUGIN_NAME = "codex-macos-notifier"


def env_get(*names: str, default: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            return value
    return default


STATE_DIR = Path.home() / ".codex" / "memories" / PLUGIN_NAME
STATE_FILE = STATE_DIR / "last_stop_notification.json"
DEDUP_WINDOW_SEC = int(
    env_get(
        "CODEX_MACOS_NOTIFIER_STOP_DEDUP_SEC",
        "CODEX_MACOS_NOTIFIER_DEDUP_SEC",
        default="120",
    )
)
DEFAULT_TITLE = "Codex Finished"
DEFAULT_SUBTITLE = "Reply complete"
DEFAULT_GROUP = "codex-macos-notifier-finished"


def main() -> int:
    if sys.platform != "darwin":
        return 0
    if (
        env_get(
            "CODEX_MACOS_NOTIFIER_DISABLE",
            default="0",
        )
        == "1"
        or env_get(
            "CODEX_MACOS_NOTIFIER_STOP_DISABLE",
            default="0",
        )
        == "1"
    ):
        return 0

    payload = read_payload()
    turn_id = payload.get("turn_id", "") or ""
    if not turn_id:
        return 0

    message = payload.get("last_assistant_message")
    signature = hashlib.sha256(
        f"{turn_id}\n{message or ''}\n{payload.get('stop_hook_active', False)}".encode("utf-8")
    ).hexdigest()
    if is_duplicate(signature):
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    title = env_get(
        "CODEX_MACOS_NOTIFIER_STOP_TITLE",
        default=DEFAULT_TITLE,
    )
    subtitle = env_get(
        "CODEX_MACOS_NOTIFIER_STOP_SUBTITLE",
        default=DEFAULT_SUBTITLE,
    )
    body = summarize(message) if message else f"Completed turn in {display_cwd(cwd)}"
    notify(
        title,
        subtitle,
        body,
        env_get(
            "CODEX_MACOS_NOTIFIER_STOP_GROUP",
            default=DEFAULT_GROUP,
        ),
    )
    remember(signature)
    return 0


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def display_cwd(cwd: str) -> str:
    name = Path(cwd).name
    return name or cwd


def summarize(message: str | None, limit: int = 110) -> str:
    if not message:
        return "Completed turn"
    text = " ".join(message.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def is_duplicate(signature: str) -> bool:
    try:
        state = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return False
    last_sig = state.get("signature")
    last_ts = state.get("timestamp", 0)
    return last_sig == signature and time.time() - float(last_ts) < DEDUP_WINDOW_SEC


def remember(signature: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps({"signature": signature, "timestamp": time.time()}),
            encoding="utf-8",
        )
    except OSError:
        pass


def notify(title: str, subtitle: str, body: str, group: str) -> None:
    if shutil_which("terminal-notifier"):
        run(
            [
                "terminal-notifier",
                "-title",
                title,
                "-subtitle",
                subtitle,
                "-message",
                body,
                "-group",
                group,
            ]
        )
        return

    script = (
        'display notification "{}" with title "{}" subtitle "{}"'.format(
            escape_applescript(body),
            escape_applescript(title),
            escape_applescript(subtitle),
        )
    )
    run(["osascript", "-e", script])


def escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def shutil_which(binary: str) -> str | None:
    from shutil import which

    return which(binary)


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
