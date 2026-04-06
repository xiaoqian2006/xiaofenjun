#!/usr/bin/env python3
"""Install the plugin into the user's personal Codex plugin directory."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PLUGIN_NAME = "codex-macos-notifier"
PRE_TOOL_USE_HOOK_COMMAND = (
    f'/usr/bin/python3 "$HOME/plugins/{PLUGIN_NAME}/scripts/pre_tool_use_notify.py"'
)
STOP_HOOK_COMMAND = (
    f'/usr/bin/python3 "$HOME/plugins/{PLUGIN_NAME}/scripts/stop_notify.py"'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-plugin",
        help="Path to the plugin directory to install. Defaults to the parent directory of this script.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = resolve_source_plugin(args.source_plugin)
    if not source.is_dir():
        raise SystemExit(f"plugin directory not found: {source}")

    home = Path.home()
    plugin_dest = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    config_path = home / ".codex" / "config.toml"
    hooks_path = home / ".codex" / "hooks.json"

    plugin_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, plugin_dest, dirs_exist_ok=True)

    ensure_marketplace(marketplace_path)
    ensure_plugin_entry(marketplace_path)
    ensure_codex_hooks_enabled(config_path)
    ensure_hooks_file(hooks_path)

    print(f"Installed plugin to {plugin_dest}")
    print(f"Updated marketplace at {marketplace_path}")
    print(f"Ensured codex_hooks = true in {config_path}")
    print(f"Ensured hook entry in {hooks_path}")
    return 0


def resolve_source_plugin(source_plugin: str | None) -> Path:
    if source_plugin:
        return Path(source_plugin).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def ensure_marketplace(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(
        json.dumps(
            {
                "name": "local",
                "interface": {"displayName": "Local Plugins"},
                "plugins": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def ensure_plugin_entry(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("interface", {}).setdefault("displayName", "Local Plugins")
    data.setdefault("plugins", [])
    data["plugins"] = [
        entry
        for entry in data["plugins"]
        if entry.get("name") != PLUGIN_NAME
    ]

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "INSTALLED_BY_DEFAULT",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }

    data["plugins"].append(entry)

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ensure_codex_hooks_enabled(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = ""
    updated = upsert_codex_hooks_flag(text)
    path.write_text(updated, encoding="utf-8")


def ensure_hooks_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"hooks": {}}

    data.setdefault("hooks", {})
    upsert_hook_entry(
        data,
        "PreToolUse",
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": PRE_TOOL_USE_HOOK_COMMAND,
                }
            ],
        },
        {
            PRE_TOOL_USE_HOOK_COMMAND,
        },
    )
    upsert_hook_entry(
        data,
        "Stop",
        {
            "hooks": [
                {
                    "type": "command",
                    "command": STOP_HOOK_COMMAND,
                }
            ],
        },
        {
            STOP_HOOK_COMMAND,
        },
    )

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def upsert_hook_entry(data: dict, event_name: str, entry: dict, commands_to_replace: set[str]) -> None:
    event_hooks = data["hooks"].setdefault(event_name, [])
    filtered = []
    for existing in event_hooks:
        existing_hooks = existing.get("hooks", [])
        kept_hooks = [
            hook
            for hook in existing_hooks
            if not (
                isinstance(hook, dict) and hook.get("command") in commands_to_replace
            )
        ]
        if not kept_hooks:
            continue
        updated_existing = dict(existing)
        updated_existing["hooks"] = kept_hooks
        filtered.append(updated_existing)
    filtered.append(entry)
    data["hooks"][event_name] = filtered


def upsert_codex_hooks_flag(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return "[features]\ncodex_hooks = true\n"

    features_start = None
    for idx, line in enumerate(lines):
        if line.strip() == "[features]":
            features_start = idx
            break

    if features_start is None:
        if text and not text.endswith("\n"):
            text += "\n"
        return text + "\n[features]\ncodex_hooks = true\n"

    section_end = len(lines)
    for idx in range(features_start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_end = idx
            break

    for idx in range(features_start + 1, section_end):
        stripped = lines[idx].strip()
        if stripped.startswith("codex_hooks"):
            lines[idx] = "codex_hooks = true"
            return "\n".join(lines) + "\n"

    lines.insert(section_end, "codex_hooks = true")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
