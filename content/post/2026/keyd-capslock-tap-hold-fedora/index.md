---
title: "使用 keyd 在 fedora 修改 Capslock 长按短按触发信号"
description: 
date: 2026-01-18T00:21:27+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: true
tags: ['Workflow']
---

> 变成 macOS 的形状了.

```bash
sudo dnf copr enable -y alternateved/keyd
sudo dnf install keyd
sudo vim /etc/keyd/default.conf
```

修改配置如下:

```bash
[ids]
*

[main]
# timeout(A, 250, B) 的意思是：
# 如果按住小于 250ms，触发 A (f14)
# 如果按住大于 250ms，触发 B (caslock)
capslock = timeout(f14, 250, capslock)
```

然后可以在 fcitx5 设置输入法切换为 f14.
