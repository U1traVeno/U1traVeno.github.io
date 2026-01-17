---
title: "使用 keyd 在 fedora 修改 Capslock 长按短按触发信号"
description: 
date: 2026-01-18T00:21:27+08:00
image: image.png
math: 
license: 
hidden: false
comments: true
draft: false
tags: ['Workflow']
---

> *~~变成 macOS 的形状了.~~*

```bash
sudo dnf copr enable -y alternateved/keyd
sudo dnf install keyd
sudo mkdir -p /etc/keyd/
sudo vim /etc/keyd/default.conf
```

修改配置如下:

```conf
[ids]
*

[main]
# timeout(A, 250, B) 的意思是：
# 如果按住小于 250ms，触发 A (f14)
# 如果按住大于 250ms，触发 B (caslock)
capslock = timeout(f14, 250, capslock)
```

启动 keyd 系统服务

```bash
sudo systemctl enable --now keyd.service
```

然后可以在 fcitx5 设置输入法切换为 f14.

如果需要修改 keyd 配置, 修改后可以不必重启服务, 而是:

```bash
sudo keyd reload
```
