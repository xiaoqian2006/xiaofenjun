#!/usr/bin/env python3
"""Send a macOS notification for commands that are likely to require approval."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
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
STATE_FILE = STATE_DIR / "last_notification.json"
DEDUP_WINDOW_SEC = int(
    env_get(
        "CODEX_MACOS_NOTIFIER_DEDUP_SEC",
        default="90",
    )
)
DEFAULT_TITLE = "Codex Approval"
DEFAULT_SUBTITLE = "Approval likely needed"
DEFAULT_GROUP = "codex-macos-notifier-approval"

NETWORK_PATTERNS = [
    re.compile(r"\b(?:curl|wget)\b"),
    re.compile(r"\bgh\b"),
    re.compile(r"\bgit\s+(?:pull|push|fetch|clone|ls-remote|submodule\s+update)\b"),
    re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|add|update|upgrade|remove|dlx|create)\b"),
    re.compile(r"\b(?:pip|pip3|uv|poetry)\s+(?:install|sync|add|remove|publish)\b"),
    re.compile(r"\b(?:brew|port)\s+(?:install|upgrade|update|tap)\b"),
    re.compile(r"\b(?:cargo|go)\s+(?:install|get|generate)\b"),
    re.compile(r"\bdocker\s+(?:pull|build|push|login|compose\s+pull)\b"),
]

DANGEROUS_PATTERNS = [
    re.compile(r"\bsudo\b"),
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"\bgit\s+reset\b"),
    re.compile(r"\bgit\s+checkout\s+--\b"),
    re.compile(r"\blaunchctl\b"),
    re.compile(r"\bopen\b"),
    re.compile(r"\bosascript\b"),
]

MUTATING_COMMANDS = {
    "cp",
    "mv",
    "mkdir",
    "touch",
    "tee",
    "install",
    "ln",
    "chmod",
    "chown",
    "rm",
}


def main() -> int:
    if sys.platform != "darwin":
        return 0
    if (
        env_get(
            "CODEX_MACOS_NOTIFIER_DISABLE",
            default="0",
        )
        == "1"
    ):
        return 0

    payload = read_payload()
    command = payload.get("tool_input", {}).get("command", "") or ""
    cwd = payload.get("cwd") or os.getcwd()
    if not command.strip():
        return 0

    reason = classify(command, cwd)
    if not reason:
        return 0

    signature = hashlib.sha256(f"{reason}\n{command}".encode("utf-8")).hexdigest()
    if is_duplicate(signature):
        return 0

    title = env_get(
        "CODEX_MACOS_NOTIFIER_APPROVAL_TITLE",
        default=DEFAULT_TITLE,
    )
    subtitle = env_get(
        "CODEX_MACOS_NOTIFIER_APPROVAL_SUBTITLE",
        default=DEFAULT_SUBTITLE,
    )
    body = f"{reason}: {summarize(command)}"
    notify(
        title,
        subtitle,
        body,
        env_get(
            "CODEX_MACOS_NOTIFIER_APPROVAL_GROUP",
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


def classify(command: str, cwd: str) -> str | None:
    for pattern in NETWORK_PATTERNS:
        if pattern.search(command):
            return "Network or remote operation"
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return "High-risk command"
    if writes_outside_workspace(command, cwd):
        return "Write outside current workspace"
    return None


def writes_outside_workspace(command: str, cwd: str) -> bool:
    if not any(token in command for token in ("/", "~/", ">")):
        return False

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False

    if not tokens:
        return False

    first = Path(tokens[0]).name
    if first not in MUTATING_COMMANDS and ">" not in command:
        return False

    workspace = Path(cwd).resolve()
    safe_prefixes = [
        workspace,
        Path("/tmp"),
        Path.home() / ".codex" / "memories",
    ]

    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        if token.startswith("~/"):
            path = Path(token).expanduser()
        elif token.startswith("/"):
            path = Path(token)
        else:
            continue
        if not is_under_any(path, safe_prefixes):
            return True

    return False


def is_under_any(path: Path, prefixes: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for prefix in prefixes:
        try:
            resolved.relative_to(prefix.resolve())
            return True
        except ValueError:
            continue
    return False


def summarize(command: str, limit: int = 110) -> str:
    text = " ".join(command.strip().split())
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
        'display notification "{}" with title "{}" subtitle "{}"'
        .format(escape_applescript(body), escape_applescript(title), escape_applescript(subtitle))
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
