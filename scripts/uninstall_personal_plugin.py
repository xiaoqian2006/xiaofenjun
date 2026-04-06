#!/usr/bin/env python3
"""Uninstall the personal Codex plugin and clean related configuration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


PLUGIN_NAMES = ["codex-macos-notifier"]
HOOK_COMMANDS = {
    f'/usr/bin/python3 "$HOME/plugins/{name}/scripts/pre_tool_use_notify.py"'
    for name in PLUGIN_NAMES
}
HOOK_COMMANDS.update(
    {
        f'/usr/bin/python3 "$HOME/plugins/{name}/scripts/stop_notify.py"'
        for name in PLUGIN_NAMES
    }
)


def main() -> int:
    home = Path.home()
    remove_plugin_dirs(home / "plugins")
    clean_marketplace(home / ".agents" / "plugins" / "marketplace.json")
    hooks_remaining = clean_hooks(home / ".codex" / "hooks.json")
    maybe_disable_codex_hooks(home / ".codex" / "config.toml", hooks_remaining)
    print("Removed personal macOS notifier plugin files and configuration.")
    return 0


def remove_plugin_dirs(parent: Path) -> None:
    for plugin_name in PLUGIN_NAMES:
        path = parent / plugin_name
        if path.exists():
            shutil.rmtree(path)


def clean_marketplace(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])
    data["plugins"] = [entry for entry in plugins if entry.get("name") != PLUGIN_NAMES[0]]
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def clean_hooks(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    hooks = data.get("hooks", {})
    cleaned_hooks = {}
    for event_name, event_entries in hooks.items():
        filtered_entries = []
        for entry in event_entries:
            entry_hooks = entry.get("hooks", [])
            kept_hooks = [
                hook
                for hook in entry_hooks
                if not (
                    isinstance(hook, dict) and hook.get("command") in HOOK_COMMANDS
                )
            ]
            if not kept_hooks:
                continue
            updated_entry = dict(entry)
            updated_entry["hooks"] = kept_hooks
            filtered_entries.append(updated_entry)
        if filtered_entries:
            cleaned_hooks[event_name] = filtered_entries

    if cleaned_hooks:
        data["hooks"] = cleaned_hooks
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return any(cleaned_hooks.get(name) for name in cleaned_hooks)

    path.write_text(json.dumps({"hooks": {}}, indent=2) + "\n", encoding="utf-8")
    return False


def maybe_disable_codex_hooks(path: Path, hooks_remaining: bool) -> None:
    if hooks_remaining or not path.exists():
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    result = []
    in_features = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_features = stripped == "[features]"
            result.append(line)
            continue
        if in_features and stripped.startswith("codex_hooks"):
            continue
        result.append(line)

    path.write_text("\n".join(result).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
