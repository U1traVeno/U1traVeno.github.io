---
layout:     post
title:      "在Linux配置Anaconda环境"
subtitle:   "隔离项目环境是好文明"
date:       2024-08-14
author:     "U1traVeno"
header-img: "img/tag-bg.jpg"
tags:
    - Linux
    - Python
---

准备把开发完全转移到linux上。windows就留着打游戏用吧。

AUR中就有Anaconda
```shell
yay -S anaconda
```
之前是在Windows上写Python的，当时用的是图形化傻瓜安装。~~一行指令就安装好conda也挺傻瓜的~~  

新建一个环境吧。网上一查，都说直接`conda create`就好了，然而刚安装找不到conda指令，需要手动设置一下.        
```shell
# 把conda的路径写到.zshrc里面
echo 'export PATH="/opt/anaconda/bin:$PATH"' >> ~/.zshrc
# 之后重启一下shell
```

这个时候conda已经可以正常用了

```shell
conda create -n <env-name>
# 列出目前已创建的所有环境
conda info --envs
```
创建环境等圈圈转完就行.然后在vscode里面指定python环境即可。  
Ctrl+Shift+P，搜索Python Select Interpreter,选择相应的环境就行
之后该装啥库装一装就能用了
