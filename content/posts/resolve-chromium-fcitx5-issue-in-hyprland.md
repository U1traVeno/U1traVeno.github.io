---
date: '2025-03-04T11:31:29+08:00'
draft: false
title: '修复hyprland中fcitx5在chromium系软件无法使用的问题'
---

这几天给台式机折腾hyprland踩过如题的坑。解决办法是给启动参数加上参数`--enable-wayland-ime`。

这里以 VScode 为例。

从`/usr/share/applications/`把`code.desktop`复制到`~/.local/share/applications/`。
因为习惯上前者应该是只读的，而系统会优先选择 ~/.local/share/applications/ 目录中的 .desktop 文件。

```shell
❯ cp /usr/share/applications/code.desktop ~/.local/share/applications
```

找到文件中Exec那一行，加上`--enable-wayland-ime`即可。

参考: [**Archlinux论坛:linuxqq无法使用输入法**](https://bbs.archlinuxcn.org/viewtopic.php?id=14347)