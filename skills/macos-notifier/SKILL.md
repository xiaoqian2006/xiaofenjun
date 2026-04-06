---
name: macos-notifier
description: Explain or troubleshoot the codex-macos-notifier plugin that sends macOS notifications before risky Bash commands and when a Codex turn finishes.
---

# macOS Notifier

Use this skill when the user asks why the notifier fired, how it decides a command is risky, how turn-finished notifications work, or how to tune its behavior.

## What it does

- The plugin installs a `PreToolUse` hook for the Bash tool.
- That hook inspects the pending shell command and sends a macOS notification for commands that are likely to trigger approval.
- The plugin also installs a `Stop` hook that sends a macOS notification when a Codex turn finishes.
- The detector is heuristic. It currently alerts for:
  - network and remote operations
  - high-risk commands such as `sudo`, `rm -rf`, and `git reset`
  - mutating commands that reference paths outside the current workspace

## Limits

- Codex does not currently expose a dedicated `ApprovalRequested` hook, so pre-approval notifications are best-effort rather than exact.
- The hook currently covers Bash tool use. Connector and MCP approvals are outside this hook's direct visibility.
- `Stop` is turn-scoped. It notifies when the current Codex reply finishes, not when the whole session exits.

## Tuning

- Set `CODEX_MACOS_NOTIFIER_DISABLE=1` to disable notifications temporarily.
- Set `CODEX_MACOS_NOTIFIER_STOP_DISABLE=1` to disable only turn-finished notifications.
- Set `CODEX_MACOS_NOTIFIER_DEDUP_SEC=<seconds>` to change duplicate suppression.
- Set `CODEX_MACOS_NOTIFIER_STOP_DEDUP_SEC=<seconds>` to change duplicate suppression for turn-finished notifications.
- Set `CODEX_MACOS_NOTIFIER_APPROVAL_TITLE` or `CODEX_MACOS_NOTIFIER_APPROVAL_SUBTITLE` to customize approval notifications.
- Set `CODEX_MACOS_NOTIFIER_STOP_TITLE` or `CODEX_MACOS_NOTIFIER_STOP_SUBTITLE` to customize turn-finished notifications.
- Set `CODEX_MACOS_NOTIFIER_APPROVAL_GROUP` or `CODEX_MACOS_NOTIFIER_STOP_GROUP` if you want independent notification replacement behavior.
