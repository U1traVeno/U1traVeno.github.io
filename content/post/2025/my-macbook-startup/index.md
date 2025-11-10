---
title: "Macbook 上手 - 基础使用和开发环境搭建"
date: 2025-11-10T02:00:00+08:00
image: image.png
math: 
hidden: false
comments: true
draft: false
tags: ['macOS', 'Workflow']
---

入手了 Macboook Air M4，感觉是受益非常大的一次购买。

此前习惯使用的开发环境是，台式机 + x86笔记本的 Archlinux。主要痛点有两个。

一是续航问题，也是最大的痛点。宿舍环境并不适合工作，因此我从起床到踩着门禁回宿舍基本不想呆在宿舍。经常的情况是，上课上一半电脑没电，只能听课。或者电脑没电，被迫回宿舍用台式，耳边是舍友游戏，同时还得时刻听网课等签到码，这种情况下其实根本无法专注开发。尝试使用平板串流回宿舍，但网络波动严重。使用平板 termux + neovim，配置太折腾，且最终体验并不好，不希望大部分时间用来配置环境而不是用来开发。

二是环境问题。Archlinux 包管理器的确方便。但不管怎样我仍然承担太多关于我自己的电脑系统运维和配置的任务，需要关注各种开发无关的事情，诸如 KDE 桌面可能滚炸，某个驱动不能直接 Syu 需要另外配置等等。只要出现一次桌面滚炸，往往意味着一个整个下午甚至更长时间都不能用于开发而是修环境，意味着延误开发进度，如果正逢 DDL，那么就死了。Archlinux 更适合有大量空闲时间可以用来精心配置自己的系统的人。Nix 这一套其实可能不错，但感觉上手需要大量时间，配置同样又要时间。有考虑过从 Archlinux 切换到 Fedora，但这同样需要我花时间，用于数据备份，重装系统，重新配置整个环境。

Macbook Air 解决了我两个最大的痛点。

本文记录了入手 Macbook 之后，我怎样搭建了我的开发环境，把它变成了一台生产力机器。

## 桌面操作和配置

### 触控板操作

设置中搜索“触控板手势”看到所有的触控板操作。

很喜欢 macOS 的全屏应用管理。三指上滑调度中心，左右横扫切换全屏应用，比较舒适。

### 键盘

macOS 中的 control, option, command 逻辑大致是：

Command (⌘)：在 macOS 里是主修饰键。你在 Windows/Linux 里平常用 Ctrl+C / Ctrl+V，到了 mac 上就是 ⌘C / ⌘V。所以 语义角色 上 Command ≈ Ctrl（别的系统的）。

Control (⌃)：是更底层的控制信号键，确实就是发 Ctrl 字符给终端那种。在 shell 或 vim 里，Ctrl+A / Ctrl+E 就是走 Emacs 控制序列那一套。

Option (⌥)：等价于 Alt。区别在于它默认还参与输入法（比如打出特殊符号或中文输入法的候选），在终端里要当作真正的 Alt 用，需要在终端设置里打开 “Use Option as Meta key”。

这样的划分其实很不错，Shell 里 Ctrl+C 不会和 ⌘C 打架。

#### 输入法

添加输入法和更改其设置，选取苹果菜单  >“系统设置”，然后点按边栏中的“键盘” 。（你可能需要向下滚动。）前往“文字输入”，然后点按“编辑”。

#### 快捷键

设置 -> 键盘 -> 键盘快捷键

可以在其中看看 macOS 的窗口管理操作快捷键。

#### fn lock

键盘快捷键 -> 将 F1, F2 等用作标准功能键

开启后调整亮度等需要按住 fn + f1。

#### fn 切换输入法，中/英 改为 Capslock

默认 fn 键是打开表情符号选单。我喜欢让它变为更改输入法，作为一个单独按键，不管怎样都不会和 shift，ctrl，ctrl+space(VSCode 的补全) 这三个其他软件常用的快捷键打架了，属于是我在 Windows 上没能解决的一个问题。 打开表情选单使用`⌘ ⇧ .`（使用 Raycast）

键盘 -> 键盘快捷键 -> 输入法，将“选择上一个输入法”和“选择‘输入法’菜单中的下一个输入法”取消勾选。

键盘 -> 按下 fn 键时 -> 更改输入法。

键盘 -> 文字输入 -> 输入法 -> 编辑 -> 所有输入法 -> 使用 中/英 键切换 ABC 输入法

这里的逻辑其实是，fn 键切换 ABC 和 拼音，而在拼音输入法中，按下中英键仍然切换中英文，但是这是在中文输入法中输入英文。

## 包管理

使用 [Homebrew](https://brew.sh/)。macOS 上最方便的包管理器，我的软件安装几乎完全由它完成，没有使用过 app store。

macOS 上还可以使用 nix 包管理器，等到有闲工夫折腾的时候试试迁移到上面。

⌘ + Space 打开终端

```zsh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

以后基本上只要 `brew install`, `brew upgrade`, `brew search`就行。

## 安装字体

```zsh
brew install font-jetbrains-mono-nerd-font
```

## 开发环境

### macOS 的文件系统

macOS 和 linux 都是 Unix，但区别其实还是有挺多。列出几点。

#### 大小写敏感

默认 macOS（APFS）是不区分大小写的，foo.txt 和 Foo.txt 是同一个文件，所以代码库如果有类似文件名（尤其前端资源、模块名），在 macOS 上可能不会报错，但在 Linux 部署就炸。

#### .DS_Store

Finder 会在每个目录下生成 .DS_Store 文件，用于存储该目录的显示设置等信息。如果不想让 git 提交这些文件，可以在全局 gitignore 里添加一行 `.DS_Store`。

```zsh
git config --global core.excludesfile ~/.gitignore_global
echo ".DS_Store" >> ~/.gitignore_global
```

总之就是不要用 Finder，这个东西防不胜防。

#### 符号链接与文件元信息

macOS 文件系统支持"扩展属性(xattrs)" 与"资源分叉resource fork"，一些工具(尤其是 Finder)会携带 `._filename` 的元文件。

使用 macOS 的 Finder 压缩一个文件夹：

```text
foo/
└── bar.txt
```

结果生成的 zip 里会有：

```text
bar.txt
__MACOSX/
__MACOSX/foo/._bar.txt
```

这些 ._bar.txt 就是存资源分叉或扩展属性的。总之不要用 Finder。

#### 路径与权限模型

macOS 路径中 / 一样分隔，但默认用户家目录权限比 Linux 更严格（SIP 保护 + sandbox）。

`/usr`(除了`/usr/local`), `/System`, `/bin`, `/sbin` 等在 macOS 是受保护的系统卷，即使 root 都不能随便写。

推荐把开发环境放在 `/usr/local` 或 `$HOME/.local` 下。

### Shell

macOS 默认使用 zsh。

#### Zim Framework

另见这一篇文章：[我的 Zim Framework 安装和配置](https://v3n0.top/post/2025/zim-makes-my-life-easier/)

#### lazyGit

[lazygit](https://github.com/jesseduffield/lazygit) 是非常好用的 Git TUI，我很爱用。

```zsh
brew install lazygit
```

我个人非常常用，所以给它加个别名

```zsh
echo "alias lg='lazygit'" >> ~/.zshrc
```

#### Yazi

[Yazi](https://yazi-rs.github.io/) 是终端文件管理器。

```zsh
brew install yazi
```

### Alacritty

[Alacritty](https://alacritty.org/) 是一个终端模拟器，轻量好用且非常非常快，极简，没有携带任何提供终端以外的功能(分屏，标签页）。如果更喜欢终端分屏而不是 tmux 的话建议另行使用 kitty。

#### 设置字体

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

#### option 键映射为 alt

```toml
# ~/.config/alacritty/alacritty.toml

[window]
option_as_alt = "Both"
```

#### ssh 到 RHEL 等系统的渲染错误问题

当你在本机运行 Alacritty 并 SSH 到远程主机时，本机的 Alacritty 会设置环境变量：`TERM=alacritty`。这告诉远程系统：“我是一个叫 alacritty 的终端，请用这个类型的渲染方式来处理颜色、光标移动、退格、清屏等控制序列。”

但问题是 Red Hat 默认的 /usr/share/terminfo 里没有 alacritty 这个定义。

所以它看到 $TERM=alacritty 时，只能“随便猜”或者退回到某种兼容模式（通常是 dumb、xterm 或 vt100），导致：

- 颜色错乱（它不理解 256 色甚至 true color 的控制码）

- Backspace 逻辑不对（字符删除信号被解释成插入空格）

- 提示符/补全的高亮样式全变色（因为属性码错位）

```zsh
infocmp alacritty > alacritty.info
scp alacritty.info user@rhel:/tmp/
ssh user@rhel
tic -x /tmp/alacritty.info
```

### 容器

macOS 上无法直接使用 linux 内核功能，因此容器和 windows 一样需要使用虚拟机实现，因此 macOS 上的容器不仅需要 CLI 还需要虚拟机 daemon。

最主流的容器虚拟机的选择是 Docker Desktop + Docker CLI

```zsh
brew install --cask docker # Docker Desktop
brew install docker docker-compose # Docker CLI 和 compose
```

虽然所有的操作完全可以使用 docker CLI 完成，但它总归会让人需要见到 GUI。

如果想纯 CLI，macOS 上另一个容器虚拟机的比较流行的选择是开源的 [colima](https://github.com/abiosoft/colima)

```zsh
brew install docker docker-compose colima
```

需要启动容器前，可以 `colima start`，不需要的时候 `colima stop`。毕竟是虚拟机，平时不用的时候可以稍微省点电。

另一个选择是 Orbstack，个人免费使用但有少些限制，商业付费。据说比 colima 使用体验丝滑很多，但我还没尝试过。目前 colima 对我来说够用。

## 其他效率工具

下面的工具只有 Raycast 是我常用的，另外几个我还没折腾过。

### Raycast

Raycast 是 macOS 上的一款快速启动器，表面看似乎只是 Spotlight 的替代品（即 ⌘ Space），但实际上更像一个开发者取向的系统操作平台，可以说是用键盘控制 macOS 的一切。不仅能打开应用、搜索文件，还能直接操作系统功能、运行命令、调用 API、触发脚本、访问第三方服务。
所有操作几乎都通过快捷键完成。

个人使用免费，功能完整。Pro 订阅才包括云同步、AI 助手、共享命令等功能，不过这些功能都可有可无，免费版已经足够强大。

### Hammerspoon

可以 lua 脚本接管各种系统级别输入，使得 macOS 实际上也可以被高度定制化。比如让窗口自动平铺、对齐、调整大小、移动到指定屏幕，监听 Wi-Fi 状态切换、USB 设备插拔、屏幕变化、甚至电量和音量事件，然后自动执行脚本。

### BetterTouchTool

能拦截 Force Click、三指手势等，并重新映射，但是收费。

### Scroll Reverser

专门分开触控板和鼠标滚轮的滚动方向。

### Karabiner-Elements

能改键盘、鼠标、触控板底层事件。
