# codex-macos-notifier

中文文档：[`README.zh-CN.md`](./README.zh-CN.md)

`codex-macos-notifier` is a macOS-only Codex plugin that sends local system notifications in two cases:

- when Codex is about to run a Bash command that is likely to require approval
- when a Codex turn finishes

It is designed for people who run Codex in the terminal and want passive desktop notifications while they are away from the keyboard.

## Features

- `PreToolUse` notification for risky Bash commands
- `Stop` notification when a Codex reply finishes
- separate notification titles, subtitles, and dedup windows for approval-like and completion events
- local-only implementation using `terminal-notifier` when available and `osascript` as fallback
- one-command install and uninstall scripts

## Requirements

- macOS
- Codex with hooks support
- Python 3 available at `/usr/bin/python3`

## Installation

Clone the repository and run:

```bash
./install.sh
```

The installer copies the plugin into `~/plugins/codex-macos-notifier`, ensures `codex_hooks = true` in `~/.codex/config.toml`, and updates `~/.codex/hooks.json`.

## Uninstall

```bash
./uninstall.sh
```

This removes the installed plugin from `~/plugins/codex-macos-notifier` and cleans its hook entries from `~/.codex/hooks.json`.

## Upgrade

After pulling new changes, run:

```bash
./install.sh
```

## Configuration

Approval notifications:

- `CODEX_MACOS_NOTIFIER_DISABLE=1` disables all notifications
- `CODEX_MACOS_NOTIFIER_DEDUP_SEC=<seconds>` changes approval dedup timing
- `CODEX_MACOS_NOTIFIER_APPROVAL_TITLE=<text>` overrides the approval notification title
- `CODEX_MACOS_NOTIFIER_APPROVAL_SUBTITLE=<text>` overrides the approval notification subtitle
- `CODEX_MACOS_NOTIFIER_APPROVAL_GROUP=<group>` changes the `terminal-notifier` group id

Turn-finished notifications:

- `CODEX_MACOS_NOTIFIER_STOP_DISABLE=1` disables only turn-finished notifications
- `CODEX_MACOS_NOTIFIER_STOP_DEDUP_SEC=<seconds>` changes turn-finished dedup timing
- `CODEX_MACOS_NOTIFIER_STOP_TITLE=<text>` overrides the turn-finished notification title
- `CODEX_MACOS_NOTIFIER_STOP_SUBTITLE=<text>` overrides the turn-finished notification subtitle
- `CODEX_MACOS_NOTIFIER_STOP_GROUP=<group>` changes the `terminal-notifier` group id

## How it works

- `hooks.json` installs a `PreToolUse` hook for the `Bash` tool
- `scripts/pre_tool_use_notify.py` classifies commands heuristically and only notifies for risky cases
- `hooks.json` also installs a `Stop` hook
- `scripts/stop_notify.py` sends a notification when the current Codex turn completes

## Limits

- approval detection is heuristic, because Codex does not expose a dedicated approval-requested hook
- approval notifications currently only cover the `Bash` tool
- completion notifications are turn-scoped, not full-session scoped
- connector and MCP approvals are outside this plugin's direct visibility

## Development

Useful commands while iterating:

```bash
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile scripts/*.py
./install.sh
```

## Repository layout

```text
.codex-plugin/plugin.json
hooks.json
install.sh
uninstall.sh
scripts/
skills/
```

## Privacy

This plugin does not send network requests. It only reads Codex hook payloads and triggers local macOS notifications.

## Terms

This repository is provided as-is. Review and test it before using it in your own Codex environment.

## Publishing checklist

- replace placeholder metadata in `.codex-plugin/plugin.json`
- choose a license before publishing publicly
- push the repository to GitHub
