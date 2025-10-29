---
title: "我的 Zim Framework 安装和配置"
date: 2025-10-27T15:32:11+08:00
draft: false
tags: ['macOS', 'zim', 'Workflow']
comments: true
---

初次知道 zim 是在 [Archlinux 简明指南](https://arch.icekylin.online/guide/advanced/beauty-3.html#_2-zsh-%E7%BE%8E%E5%8C%96)。体感上确实比 Oh-my-zsh 快一些，主要快在启动速度。这一点在使用 tmux 之类的时候，频繁创建关闭终端，体感上会比较明显。

之前 Arch 上的 zim 配置了什么东西没有记下来，早就忘了，没记错的话就几乎只是跟着上面的教程装了个 p10k。现在入手了 Macbook air，准备把自己的工作流配置都记录一下。这篇博客会是其中的一篇。

------

## Zim 安装

Zim Framework 官网上的指令:

```zsh
curl -fsSL https://raw.githubusercontent.com/zimfw/install/master/install.zsh | zsh
```

重进终端，可以看到终端样式已经变了。`.zshrc` 文件中也多出了 zim 生成的配置内容。大部分一般不用更改。我习惯把编辑模式改成 vi 模式：

```zsh
# ~/.zshrc

# Set editor default keymap to emacs (`-e`) or vi (`-v`)Vj
bindkey -v
```

同时 zim 安装后创建了 `.zimrc`。zim 插件的安装方式基本上就是，在这里面加 zmodule，然后 `zimfw install` 一下。

一般只要仓库根目录存在一个可以被 source 的 `.zsh` 文件，就可以被视作一个 zmodule。只要在 `.zimrc` 添加: `zmodule author/repo`，然后 zim 会自己 clone, 加载。

zim 默认提供了很多指令别名。见: [Zim Framework Docs - Cheatsheet](https://zimfw.sh/docs/cheatsheet/)。个人不常用。

## 插件配置

### powerlevel10k

一个比较好用的 zsh 主题。已经停止维护但够稳定好用。以后也许会试试 Starship，但我懒得折腾。

想通过 zim 安装其他插件

安装前建议先安装 JetBrainsMono Nerd Font。

我使用 Alacritty，设置字体可以修改 `~/.config/alacritty/alacritty.toml`

```toml
# ~/.config/alacritty/alacritty.toml

[font]
size = 16.0

[font.normal]
family = "JetBrainsMono Nerd Font"
style = "Regular"

[font.bold]
family = "JetBrainsMono Nerd Font"
style = "Bold"

[font.italic]
family = "JetBrainsMono Nerd Font"
style = "Italic"

[font.bold_italic]
family = "JetBrainsMono Nerd Font"
style = "Bold Italic"
```

要使用 zim 安装 p10k，在 .zimrc 中添加：

```zsh
# ~/.zimrc
zmodule romkatv/powerlevel10k --use degit
```

然后 `zimfw install`，并重启终端。会进入 p10k 的初始化配置流程。选择自己喜欢的样式。

### fzf

[fzf](https://junegunn.github.io/fzf/) 是一个通用的命令行模糊查找工具。

首先需要安装 fzf。

```zsh
brew install fzf
```

之后在终端中输入 fzf 会发现已经可用。

基本上，你可以将 fzf 视为“grep”的交互式版本，我们现在只是安装了这个程序。

根据 fzf 文档，我们可以[在 Shell 中集成 fzf](https://junegunn.github.io/fzf/shell-integration/)，可以用到一些好用的快捷键。官方文档的方式是在 `.zshrc` 中添加 `source <(fzf --zsh)`。

但使用 zim 管理，我们可以在 `.zimrc` 中添加：

```zsh
# ~/.zimrc

# fzf 
zmodule fzf
zmodule Aloxaf/fzf-tab
```

其中第二个插件可以让 fzf 接管终端中的 tab 操作。

现在可以使用文档中描述的快捷键了。

对于 macOS，其中的 Alt+C 尝试用 option+C 会发现输入的是 C 的特殊字符。实际上，会发现可以用 esc+C 或者先按 ESC 再按 C 来替代。早年终端没有独立的 Alt 键，有人约定 Alt+X 等同于先发一个 ESC 再发一个 X。后面为了兼容依旧沿用这个设定。

我使用的是 alacritty，可以添加以下配置

```toml
# ~/.config/alacritty/alacritty.toml

[window]
option_as_alt = "Both"
```

### 语法高亮

据 [TheCW 的一个视频](https://www.bilibili.com/video/BV1fdTfzeE8X/?share_source=copy_web&vd_source=02c8907d23d01f0c75f46a7c1a61accf)所说，用这个语法高亮会更快一点。我跟风做了。

```zsh
# ~/.zimrc

# zmodule zsh-users/zsh-syntax-highlighting
zmodule zdharma-continuum/fast-syntax-highlighting
```

------

更多的插件可以自己探索一下。比如看看 [Zim Framework - Module](https://zimfw.sh/docs/modules/), 看看有什么官方维护的 Zim 插件，或是看看别的技术佬用了啥。对我自己而言，已经不想再折腾这那，够用了就行。
