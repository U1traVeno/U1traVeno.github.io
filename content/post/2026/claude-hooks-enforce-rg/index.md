---
title: "用 Claude Code Hook 强制使用 rg 替代 grep"
description:
date: 2026-02-28T20:00:00+08:00
image:
math:
license:
hidden: false
comments: true
draft: false
tags: ['Claude Code', 'Workflow', 'ripgrep']
---

Claude Code 内置了专用的 grep 工具，但在某些场景下它仍会通过 Bash 工具直接调用 `grep`。ripgrep（`rg`）在速度、默认递归搜索、自动遵守 `.gitignore` 等方面都更优。通过配置 PreToolUse hook，可以让 Claude Code 在执行任何 grep 命令时自动切换为 rg。

## Claude Code Hooks 工作原理

Claude Code 支持在特定事件点注入用户脚本，称为 hooks。`PreToolUse` 事件在工具调用执行**之前**触发，可以检查、拦截即将执行的操作。

对于 Bash 工具，hook 脚本通过 stdin 接收如下 JSON：

```json
{
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_input": {
    "command": "grep -r 'pattern' ."
  }
}
```

hook 脚本可以输出以下 JSON 来拦截命令：

```json
{
  "decision": "block",
  "reason": "原因说明，Claude 会读取并据此调整"
}
```

**关键机制**：hook 无法直接修改命令本身，只能 block 并附带说明。Claude 读取 reason 后会自动纠正并重试——这已经足够实现目标。

## 实现步骤

### 1. 创建 hook 脚本

新建 `~/.claude/hooks/grep-to-rg.sh`：

```bash
#!/bin/bash
# 拦截 grep 命令，提示 Claude 改用 rg

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -qE '(^|[|;&]\s*|`\s*)grep\b'; then
  jq -n '{
    "decision": "block",
    "reason": "禁止使用 grep。请改用 ripgrep (rg)，例如将 grep -r 替换为 rg，grep -l 替换为 rg -l。rg 更快且默认递归搜索。"
  }'
  exit 0
fi
```

正则 ``(^|[|;&]\s*|`\s*)grep\b`` 覆盖了命令开头、管道、分号、反引号等各种 grep 出现的位置，避免误拦截含 "grep" 字符串的变量名等。

赋予执行权限：

```bash
chmod +x ~/.claude/hooks/grep-to-rg.sh
```

### 2. 注册到 settings.json

编辑 `~/.claude/settings.json`，添加 hooks 配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/your-name/.claude/hooks/grep-to-rg.sh"
          }
        ]
      }
    ]
  }
}
```

`matcher: "Bash"` 表示仅对 Bash 工具调用触发此 hook。

## 验证

用 echo 模拟 stdin，测试脚本逻辑：

```bash
# grep 命令应被拦截
echo '{"tool_input":{"command":"grep -r pattern ."}}' \
  | ~/.claude/hooks/grep-to-rg.sh

# 输出：
# {
#   "decision": "block",
#   "reason": "禁止使用 grep。..."
# }

# rg 命令应静默通过
echo '{"tool_input":{"command":"rg pattern ."}}' \
  | ~/.claude/hooks/grep-to-rg.sh; echo "exit: $?"

# 输出：
# exit: 0
```

重启 session 后，让 Claude 尝试执行一个 grep 命令，它会自动切换为 rg：

```bash
# 尝试 grep
grep -r "PluginList" Plugins/
# → hook 触发，被拦截

# Claude 自动改用 rg
rg "PluginList" Plugins/
# → 正常执行，返回结果
```

## 补充说明

- **作用范围**：配置在 `~/.claude/` 为用户级，对所有项目生效。若只想对特定项目生效，将 hooks 配置放到项目的 `.claude/settings.json` 中即可。
- **hook 不能修改命令**：PreToolUse hook 目前只支持 allow / block / ask 三种决策，无法直接改写即将执行的命令。依赖 Claude 读取 reason 后自动纠正，实际效果等价。
- **前提**：系统中需要安装 `rg` 和 `jq`。macOS 上 `brew install ripgrep jq`，其他平台参考各自的包管理器。
