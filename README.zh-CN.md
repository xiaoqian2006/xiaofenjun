# codex-macos-notifier

英文文档：[`README.md`](./README.md)

`codex-macos-notifier` 是一个仅支持 macOS 的 Codex 插件，会在以下两种场景下发送本地系统通知：

- Codex 即将执行一个大概率需要审批的 Bash 命令时
- 当前一次 Codex 对话回合结束时

这个插件适合在终端里使用 Codex、并希望离开键盘时仍能收到桌面提醒的用户。

## 功能特性

- 为高风险 Bash 命令提供 `PreToolUse` 通知
- 在 Codex 回复结束时发送 `Stop` 通知
- 为审批类通知和完成类通知分别提供标题、副标题和去重时间窗口
- 纯本地实现，优先使用 `terminal-notifier`，不可用时回退到 `osascript`
- 提供一键安装和卸载脚本

## 运行要求

- macOS
- 支持 hooks 的 Codex
- 可用的 `/usr/bin/python3`

## 安装

克隆仓库后执行：

```bash
./install.sh
```

安装脚本会把插件复制到 `~/plugins/codex-macos-notifier`，确保 `~/.codex/config.toml` 中启用了 `codex_hooks = true`，并更新 `~/.codex/hooks.json`。

## 卸载

```bash
./uninstall.sh
```

卸载脚本会删除 `~/plugins/codex-macos-notifier` 下的已安装插件，并从 `~/.codex/hooks.json` 中清理对应的 hook 配置。

## 升级

拉取最新代码后再次执行：

```bash
./install.sh
```

## 配置项

审批通知：

- `CODEX_MACOS_NOTIFIER_DISABLE=1` 关闭全部通知
- `CODEX_MACOS_NOTIFIER_DEDUP_SEC=<seconds>` 修改审批通知的去重时间
- `CODEX_MACOS_NOTIFIER_APPROVAL_TITLE=<text>` 覆盖审批通知标题
- `CODEX_MACOS_NOTIFIER_APPROVAL_SUBTITLE=<text>` 覆盖审批通知副标题
- `CODEX_MACOS_NOTIFIER_APPROVAL_GROUP=<group>` 修改 `terminal-notifier` 的 group id

回合完成通知：

- `CODEX_MACOS_NOTIFIER_STOP_DISABLE=1` 仅关闭回合完成通知
- `CODEX_MACOS_NOTIFIER_STOP_DEDUP_SEC=<seconds>` 修改回合完成通知的去重时间
- `CODEX_MACOS_NOTIFIER_STOP_TITLE=<text>` 覆盖回合完成通知标题
- `CODEX_MACOS_NOTIFIER_STOP_SUBTITLE=<text>` 覆盖回合完成通知副标题
- `CODEX_MACOS_NOTIFIER_STOP_GROUP=<group>` 修改 `terminal-notifier` 的 group id

## 工作原理

- `hooks.json` 为 `Bash` 工具安装了一个 `PreToolUse` hook
- `scripts/pre_tool_use_notify.py` 会基于启发式规则判断命令风险，只在高风险场景下通知
- `hooks.json` 同时安装了 `Stop` hook
- `scripts/stop_notify.py` 会在当前 Codex 回合完成后发送通知

## 已知限制

- 审批检测依赖启发式规则，因为 Codex 目前没有直接暴露“请求审批”的专用 hook
- 审批通知目前只覆盖 `Bash` 工具
- 完成通知的作用范围是单次回合，不是整个会话
- Connector 和 MCP 的审批行为不在这个插件的直接可见范围内

## 开发

迭代时常用命令：

```bash
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile scripts/*.py
./install.sh
```

## 仓库结构

```text
.codex-plugin/plugin.json
hooks.json
install.sh
uninstall.sh
scripts/
skills/
```

## 隐私

这个插件不会发送网络请求。它只会读取 Codex hook 的负载，并触发本地 macOS 通知。

## 使用条款

本仓库按现状提供。在用于你自己的 Codex 环境前，请先自行审阅并测试。

## 发布前检查清单

- 替换 `.codex-plugin/plugin.json` 中的占位元数据
- 公开发布前先选择许可证
- 将仓库推送到 GitHub
