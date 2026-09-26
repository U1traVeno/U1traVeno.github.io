---
title: "在 SSH + tmux 里给 Claude Code 粘贴 Mac 剪贴板里的图片"
description: "Claude Code 跑在远端 Linux 上时 Ctrl+V 贴不了本地截图。用一个假 xclip 加 SSH 反向转发把 Mac 的剪贴板接过去。"
date: 2026-09-26T21:04:29+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: false
tags: ['Workflow', 'Claude Code']
---

我的环境：MacBook 上 kitty → tmux → `ssh` → Fedora homelab 上的 tmux → Claude Code。截图后按 Ctrl+V，什么都贴不进去。

## 原因

Claude Code 在 Linux 上贴图，是在它自己所在的机器上调用这些命令：

```sh
xclip -selection clipboard -t TARGETS -o | grep -E "image/(png|jpeg|...)" || wl-paste -l | grep ...
xclip -selection clipboard -t image/png -o > file || wl-paste --type image/png > file
```

它读的是远端机器的 X11/Wayland 剪贴板，而 homelab 是 headless 的。kitty、tmux、SSH 之间只传字节流，OSC 52 也只管文本，所以不管这几层怎么配都没用。能下手的地方只有这个 `xclip`。

## 思路

- 每条 SSH 连接都把远端的 `127.0.0.1:47851` 反向转发到 **Mac 自己的 sshd**。
- 远端放一个假的 `xclip`，通过这条隧道 `ssh` 回 Mac，在 Mac 上执行 `pngpaste -`。

绕一圈走 sshd，而不是在 Mac 上开一个吐剪贴板的小服务，原因是远端有好几个账号，回环端口谁都能连。走 sshd 的话，只有 Mac 授权过的 key 能进来；再把 host key 钉死，别的账号就算抢先占了这个端口，也收不到这条连接。这样 Mac 上也不需要常驻任何进程。

用 TCP 而不用 Unix socket 转发，是因为 socket 在连接断开后会留下残留文件，下次绑定会失败，除非服务端开了 `StreamLocalBindUnlink`。

## Mac 端

打开「远程登录」，把远端账号的公钥加进 `~/.ssh/authorized_keys`，再装上 `pngpaste`（brew 或 nixpkgs 都有）。

`~/.ssh/config`：

```sshconfig
Host thinkpad thinkpad-local
  RemoteForward 127.0.0.1:47851 localhost:22
```

同时开多条连接时，后连上的那条会报 `remote port forwarding failed`。这不影响使用，先连上的那条仍在提供同一个剪贴板。

## 远端

单独准备一份 known_hosts，里面只放 Mac 的 host key：

```text
# ~/.config/clipbridge/known_hosts
[127.0.0.1]:47851 ssh-ed25519 AAAA...
```

再放一个 `xclip` 到 PATH 里，要排在真正的 xclip 前面（headless 机器上一般本来就没装），比如 `~/.local/bin/xclip`：

```bash
#!/usr/bin/env bash
selection=clipboard target="" output=""
while [ $# -gt 0 ]; do
  case "$1" in
    -selection|-sel) selection=$2; shift ;;
    -t|-target) target=$2; shift ;;
    -o|-out) output=1 ;;
  esac
  shift
done

# 只桥接"读 clipboard"
if [ "$selection" != clipboard ] || [ -z "$output" ]; then
  echo "xclip: only 'xclip -selection clipboard [-t ...] -o' is bridged to the Mac" >&2
  exit 1
fi

mac() {
  ssh -p 47851 \
    -o BatchMode=yes -o ConnectTimeout=3 \
    -o UserKnownHostsFile="$HOME/.config/clipbridge/known_hosts" -o StrictHostKeyChecking=yes \
    -o ClearAllForwardings=yes \
    -o ControlMaster=auto -o ControlPersist=60 \
    -o ControlPath="$HOME/.cache/clipbridge-%C" \
    you@127.0.0.1 "$@"
}

# ~ 由 Mac 那边的 shell 展开
case "$target" in
  TARGETS) mac '~/.nix-profile/bin/pngpaste - >/dev/null 2>&1' && echo image/png ;;
  image/png) mac '~/.nix-profile/bin/pngpaste -' ;;
  ""|text/plain|UTF8_STRING|STRING) mac pbpaste ;;
  *) exit 1 ;;
esac
```

补充几点：

- `pngpaste` 的路径要按你在 Mac 上的实际安装位置改：brew 装的是 `/opt/homebrew/bin/pngpaste`。
- 贴一次图会调用两次（先查 `TARGETS`，再取 `image/png`），`ControlMaster` 让这两次复用同一条连接。
- 剪贴板里没有图片时脚本返回非零，Claude Code 会自己退回到别的处理方式。

配好后在 Mac 上重新 `ssh` 一次，让转发生效。远端的 tmux 会话不受影响，重新 attach 就行。之后截图，在 Claude Code 里 Ctrl+V 即可。

我实际是用 Home Manager 管这两边的，见 dotfiles 里的 [`hosts/thinkpad-veno.nix`](https://github.com/U1traVeno/dotfiles/blob/main/hosts/thinkpad-veno.nix) 和 [`hosts/macbook-veno.nix`](https://github.com/U1traVeno/dotfiles/blob/main/hosts/macbook-veno.nix)。
