---
layout:     post
title:      我的Archlinux配置踩坑
subtitle:   整理各种奇奇怪怪的问题
author:     U1traVeno
date:       2024-08-21
img:        img/tag-bg.jpg
tags:
    - Linux
    - 随笔
---

> 本文内容将长期更新，文章日期为第一次编辑日期

------

2024.8.21

今日算是折腾完了之前那个To-do list for my Archlinux的一部分.

#### 耗电快
这个问题已经通过tlp解决了。装上tlp效果立竿见影，已经赶上windows的省电效果了，但是还差二十分钟的样子。也许是剩余电量计算方式不同导致的。但是总想着，毕竟已经用linux了，照理来说运行的东西应该更少，功耗应该更慢才对。

不过算是能用了。也就懒得再细细折腾了。等到以后何时有闲情雅致的时候再去折腾吧。

#### zsh优化
删了出问题的组件就解决问题(好孩子不要学

#### LinuxQQ声音问题
某天yay -Syu时突然好了。

#### 美化
使用了Layan light主题，加上不知什么的好看图标。

#### 网络代理问题
V2rayA的全局透明代理总是遇到各种的问题，还是需要自己慢慢配置。
浏览器方面，GFW list模式总是在各种时候抽风，访问外网检测不到，访问大陆也检测不到，有时候干脆给我全球断网。
ChatGPT访问时检测到我是VPN,让我关掉VPN。这一问题后来查到是因为ChatGPT可以检测到透明代理。

上面的问题都可以通过给浏览器配置代理解决。
firefox搜索代理，把http[s]的代理端口改成V2rayA的20172端口即可。


