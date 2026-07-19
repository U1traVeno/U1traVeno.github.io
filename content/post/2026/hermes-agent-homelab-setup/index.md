---
title: "在 HomeLab 上搭建团队共用的 Hermes Agent"
description: "记录如何在同一台 Fedora + Nix HomeLab 上，通过 localhost SSH 为 Hermes Agent 提供独立用户环境、Home Manager 依赖与受控的工具权限。"
date: 2026-07-18T06:46:55+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: false
tags: ["Hermes Agent", "HomeLab", "Fedora", "Nix", "Home Manager", "SSH"]
---

最近，我准备在 HomeLab 上部署一个团队共用的 Hermes Agent。

这次搭建的核心思路，是让 Hermes 的 Terminal Backend 在同一台物理机上通过 `localhost` SSH 登录专用的 `hermes` 用户，而不是把 Agent 的工作环境塞进 Docker 容器，也不再额外维护一台虚拟机。这里没有第二台远程主机：Gateway 和 SSH Server 都运行在这台 Fedora HomeLab 上，SSH 只是同机切换执行身份和进入独立用户环境的边界。

选择 SSH 是因为它足够朴素：Hermes 登录后看到的是一个正常的 Linux 用户环境，`lark-cli`、GitHub CLI、Git、Nix 等需要交互式鉴权或长期保存凭据的工具都可以按常规方式配置。与此同时，Linux 用户、用户组、文件权限和 SSH 本身已经提供了一套清楚的隔离边界。

## 为什么 Terminal Backend 选择 SSH

Hermes 需要的不只是一个能执行几条 Shell 命令的临时环境。它还要长期维护自己的工作区，使用团队工具，并在多次会话之间保留必要的配置和状态。

我最初考虑过三种方案：

| 方案 | 优点 | 主要问题 |
| --- | --- | --- |
| Docker | 部署和销毁方便，文件系统边界直观 | 设备、网络、凭据和宿主工具都要额外映射；CLI 鉴权比较别扭 |
| 虚拟机 | 隔离完整，环境接近独立主机 | 太重，资源和配置都有额外维护成本 |
| SSH 到专用用户 | 环境原生，工具和鉴权方式自然，方便用 Nix 管理 | 隔离强度取决于宿主机权限配置，需要认真审计 |

Docker 对无状态服务很好用，但 Agent 的使用方式更像“一个长期在线的远程同事”。例如 `lark-cli` 和 GitHub CLI 都可能涉及浏览器登录、设备授权、凭据缓存或本地配置目录。把这些状态放进容器，需要继续处理 volume、UID、密钥注入和容器重建后的状态恢复。容器能提供隔离，但也把正常的用户环境拆成了许多需要手工连接的碎片。

虚拟机可以绕过这些问题，却又走到了另一个极端。为了一个用户态 Agent 单独维护完整操作系统，在我的 HomeLab 上有些过重。

所以最终的模型很简单。下面所有组件都位于同一台 Fedora 物理机，连接只经过 loopback：

```text
Hermes Gateway（veno 用户启动）
        │
        │ SSH localhost
        ▼
hermes 用户
├── 独立的 HOME
├── Home Manager 管理的软件环境
├── 独立的 SSH / Git / CLI 凭据
├── 可写的工作目录
└── 无 sudo 权限
```

这个方案并不等于强沙箱。它的安全性主要来自普通 Linux 用户隔离，因此后面还需要专门处理 Hermes 自带 Tools 的访问范围，防止 Gateway 进程绕开 SSH 用户边界直接读写 `veno` 的文件。

## 环境准备与用户配置

### 创建专用用户

先在 Fedora 上创建 `hermes` 用户。它需要正常的登录 Shell 和独立 Home，但不加入 `wheel`，也不应该继承 `veno` 所在的敏感用户组。

计划采用的基础操作如下，实际执行前仍要根据当前系统的用户组整理结果确认参数：

```bash
sudo useradd --create-home --shell /bin/bash hermes
sudo passwd -l hermes
id hermes
```

锁定密码不影响密钥登录，可以减少本地密码被尝试的入口。创建后需要重点检查：

- `hermes` 不属于 `wheel`；
- `hermes` 不属于可以访问容器 socket、虚拟化设备或敏感服务的组；
- `/home/veno` 不对其他用户开放；
- 团队共享目录通过专用用户组授权，而不是放宽整个 Home 目录权限。

共享目录会单独建立。例如，如果 Agent 只需要操作 `/srv/hermes-workspace`，就只把这个目录授予对应用户组，不让它顺便获得 `/srv` 下其他服务的访问权。

```bash
sudo groupadd --force hermes-workspace
sudo usermod --append --groups hermes-workspace hermes
sudo install -d \
  --owner=hermes \
  --group=hermes-workspace \
  --mode=2770 \
  /srv/hermes-workspace
```

这里的 setgid 位可以让新文件继承目录所属组，避免多人或自动化进程协作时不断出现组权限漂移。

### 配置 localhost SSH

Hermes Gateway 由同一台机器上的 `veno` 用户启动，但 Terminal Backend 通过 `localhost` 登录的是 `hermes`。两者之间使用一把专用 SSH 密钥，不复用我日常登录服务器的密钥，也不需要让这条连接暴露到局域网。

```bash
ssh-keygen \
  -t ed25519 \
  -f ~/.ssh/hermes-agent \
  -C "hermes-agent@localhost"
```

然后把公钥写入 `hermes` 的 `authorized_keys`，并严格设置目录和文件权限。这里还可以在 key 前添加 `from="127.0.0.1,::1"`，把这把密钥限制为只能从本机使用。

```text
from="127.0.0.1,::1" ssh-ed25519 AAAA... hermes-agent@localhost
```

需要注意，SSH key options 的最终写法要和 Hermes Terminal Backend 的连接方式一起验证。如果 Backend 需要端口转发、PTY 或其他能力，不能过早加上会破坏正常工作的限制。

完成后先脱离 Hermes 做一次最小连接测试：

```bash
ssh \
  -i ~/.ssh/hermes-agent \
  -o IdentitiesOnly=yes \
  hermes@localhost
```

预期结果是登录后 `whoami` 返回 `hermes`，`$HOME` 为 `/home/hermes`，并且无法读取 `/home/veno` 中权限受限的文件。

## 用 Nix 和 Home Manager 管理工作环境

我的 HomeLab 是 Fedora + Nix：Fedora 负责内核、驱动、系统服务和用户，Nix 负责用户态工具链。Hermes 也沿用这条边界。

### 为 Hermes 整理独立分组

这次不打算把我的全部 Home Manager 配置原样复制给 Hermes。个人桌面工具、私有 Shell 配置和只对我有意义的开发环境都不应该进入 Agent 的闭包。

我的 dotfiles 已经按 host 和 package module 做过一轮整理。`hosts/thinkpad-veno.nix` 负责组合我自己的完整环境，而 Hermes 使用单独的 `hosts/thinkpad-hermes.nix`。两者可以复用基础模块，但不会共享同一份 host 配置：

```text
dotfiles/
├── flake.nix
├── hosts/
│   ├── thinkpad-veno.nix
│   └── thinkpad-hermes.nix
└── modules/
    └── packages/
        ├── base.nix
        ├── node.nix
        ├── modern-unix.nix
        └── cli.nix
```

Hermes 的 host 配置只导入这四个模块：

```nix
{ ... }:
{
  imports = [
    ../modules/packages/base.nix
    ../modules/packages/node.nix
    ../modules/packages/modern-unix.nix
    ../modules/packages/cli.nix
  ];

  home = {
    username = "hermes";
    homeDirectory = "/home/hermes";
    stateVersion = "26.05";
  };

  programs.home-manager.enable = true;
}
```

其中，`base.nix` 提供 Git、curl、jq、fzf 和 Neovim 等基础工具；`modern-unix.nix` 提供 `ripgrep`、`fd`、`bat`、`eza`、`zoxide` 等现代命令行工具；`cli.nix` 安装 GitHub CLI 和 Gitea 的 `tea`；`node.nix` 则安装 Node.js、pnpm、Yarn 和 Bun，并把 npm 的用户级 prefix 设置到 `~/.local/share/npm`。

对应的 flake 输出也沿用现有的“用户@主机”命名方式：

```nix
homeConfigurations."hermes@thinkpad" = home-manager.lib.homeManagerConfiguration {
  inherit pkgs;
  modules = [ ./hosts/thinkpad-hermes.nix ];
};
```

我原来为 `lark-cli` 写过单独的 Nix package，后来把它删掉了。`lark-cli` 和 Codex 都以 npm 作为主要发布和更新方式，而且版本更新频繁。继续在 dotfiles 中维护版本号、下载地址和 hash，只会让 Nix 包长期落后于上游。因此，Home Manager 只负责提供稳定的 Node/npm 环境，这两个工具交给 `hermes` 用户通过 npm 管理：

```bash
npm install --global @larksuite/lark-cli @openai/codex
```

这里的“global”并不会写入系统目录。`node.nix` 已经把 npm prefix 指向 `/home/hermes/.local/share/npm`，并把其中的 `bin` 加入 `PATH`，所以安装和升级都不需要 sudo：

```bash
npm update --global @larksuite/lark-cli @openai/codex
```

这样划分之后，Nix 管理相对稳定的运行时和通用工具，npm 管理以 npm 为主要发布渠道、需要频繁跟进版本的 Agent CLI。Hermes 仍然拿不到宿主机的软件安装权限，只能修改自己 Home 下的 npm prefix。

Hermes Agent 本体也采用相同的判断：它更新频繁，而且官方提供了自己的安装与更新流程，所以不由 `thinkpad-hermes.nix` 管理。当前使用的是官方 Quick Install 命令：

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

因此，`hosts/thinkpad-hermes.nix` 中没有导入 `agents.nix`。Home Manager 负责准备 curl、Git、Node 和常用 CLI 等稳定基础环境；Hermes Agent、`lark-cli` 和 Codex 则分别跟随自己的主要上游渠道更新。这里的 `curl | bash` 不是由 root 执行，安装结果只进入 Hermes 用户自己的目录。即便如此，每次重新安装前仍然应该确认域名和脚本来源；方便更新不等于可以忽略供应链风险。

### 给 Hermes 一个独立的 GitHub 身份

如果 Hermes 只有 dotfiles 的只读权限，它可以在本地修改配置，却没办法把分支推到 GitHub，也就不能独立发起 PR。因此还需要给它一个可审计的 GitHub 身份。

GitHub 没有个人账号下面的子账号。按照 GitHub 对[账号类型](https://docs.github.com/en/get-started/learning-about-github/types-of-github-accounts)的说明，用于自动化的账号仍然是一个独立 user account，GitHub 称之为 machine user。它不会在账号层面从属于 `U1traVeno`，但我负责创建、保管恢复方式和控制它能访问哪些仓库。将来如果需要真正的组织归属和集中权限管理，应该建立 GitHub Organization，或者改用 GitHub App。

对于当前公开的 dotfiles 仓库，独立 machine user + fork 已经足够：

目前创建的账号是 [`U1traVeno-hermes`](https://github.com/U1traVeno-hermes)，使用独立邮箱 `hermes@v3n0.top`。这个账号只代表由我维护的 Hermes 自动化身份，不和我的日常 GitHub 登录或凭据混用。

```text
U1traVeno/dotfiles（上游，只读）
              ▲
              │ Pull Request
              │
U1traVeno-hermes/dotfiles（fork，可写）
              ▲
              │ SSH push
              │
/home/hermes/dotfiles
```

#### 创建 machine user

账号注册需要由我手动完成，不能把主账号的密码、2FA 或恢复码交给 Agent。这个账号使用独立用户名和邮箱，并在 profile 中明确标注它是由我维护的自动化账号，避免其他人把它误认为真人团队成员。

账号初始化时需要完成这些设置：

1. 使用独立的长随机密码；
2. 开启 2FA；
3. 把恢复码保存在我的密码管理器中，而不是 `/home/hermes`；
4. 添加并验证独立邮箱 `hermes@v3n0.top`；
5. 不给该账号添加主仓库 collaborator 权限；
6. 由 machine user fork `U1traVeno/dotfiles`。

即使 Hermes 的凭据泄漏，攻击者也只能修改它自己的 fork，不能直接写入上游 `main`。PR 仍然必须经过主账号审查和合并。

#### 配置 Hermes 自己的 SSH 身份

先进入同一台机器上的 `hermes` 用户并生成默认 key：

```bash
install -d -m 0700 ~/.ssh
ssh-keygen \
  -t ed25519 \
  -C "hermes@v3n0.top"
```

直接接受默认保存位置 `~/.ssh/id_ed25519`。如果这个文件已经存在，先确认它是否就是 Hermes 当前使用的身份，不要覆盖。把 `~/.ssh/id_ed25519.pub` 添加到 `U1traVeno-hermes` 的 **Settings -> SSH and GPG keys**；私钥只保留在 Hermes 自己的 Home 中。

测试时要确认 GitHub 返回的是 machine user，而不是我的主账号：

```bash
ssh -T git@github.com
```

#### 先在 Web 上 fork dotfiles

`U1traVeno-hermes` 没有 `U1traVeno/dotfiles` 的写权限，所以不能把本地分支直接推送到我的仓库。它必须先以自己的身份 fork 一份仓库，得到可写的：

```text
U1traVeno-hermes/dotfiles
```

首次 bootstrap 时，Home Manager 还没有生效，`gh` 也还没有安装，所以这里不能先写 `gh repo fork`。我直接在浏览器中登录 `U1traVeno-hermes`，打开 `U1traVeno/dotfiles` 后点击 **Fork**。

完成后可以先在 Web 页面确认下面两个仓库关系正确：

```text
nameWithOwner: U1traVeno-hermes/dotfiles
parent:        U1traVeno/dotfiles
```

后续 Hermes 只把 topic branch 推送到 `U1traVeno-hermes/dotfiles`，再以该分支为 head 向 `U1traVeno/dotfiles` 的 `main` 发起 PR。机器账号不需要成为上游仓库的 collaborator，也不需要获得上游 `Contents: write` 权限。

#### 用临时 Git bootstrap Home Manager

此时 `hermes` 的 Home Manager 配置还没有应用，所以系统里既没有 Git，也没有 `gh`。但 Nix 已经可用，可以先进入一个临时带 Git 的 Shell：

```bash
nix shell 'nixpkgs#git'
```

这个 Shell 里的 Git 只用于完成第一次 clone。因为机器账号的 fork 已经创建，而且 SSH 公钥也已经登记到 GitHub，所以直接 clone 可写的 fork：

```bash
git clone git@github.com:U1traVeno-hermes/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

仓库中的 `flake.lock` 已经固定了 Home Manager input，所以 bootstrap 时不需要再执行 `nix run github:nix-community/home-manager`。后者会解析上游的 `HEAD`，请求 GitHub commits API；在共享出口 IP 上很容易撞到匿名 API rate limit。

构建前必须先确认 host module 中的 Unix 用户名与当前实际账号完全一致：

```bash
id -un
printf '%s\n' "$HOME"
```

例如实际账号叫 `hermes-fp`，对应配置就必须是：

```nix
home = {
  username = "hermes-fp";
  homeDirectory = "/home/hermes-fp";
  stateVersion = "26.05";
};
```

Home Manager 会在 activation 时比较 `$USER` 与 `home.username`。如果当前用户是 `hermes-fp`，配置却写着 `hermes`，它会以 `USER is "hermes-fp", expected "hermes"` 拒绝执行，防止把另一个用户的配置误装进当前 Home。

`homeConfigurations` 的输出名在技术上只是 flake attribute，并不参与 Unix 权限检查，但为了避免选错目标，也应该沿用真实用户名。例如：

```nix
homeConfigurations."hermes-fp@thinkpad" =
  home-manager.lib.homeManagerConfiguration {
    inherit pkgs;
    modules = [ ./hosts/thinkpad-hermes.nix ];
  };
```

完成对应修改后，使用本地 flake 构建目标用户的 activation package。下面仍以文章中的 `hermes` 示例账号为例，实际部署时需要替换成真实输出名：

```bash
nix build '.#homeConfigurations."hermes@thinkpad".activationPackage'
./result/activate
```

这样使用的是 dotfiles 锁文件中的确切 Home Manager revision，可复现，也不需要系统中预先存在 `home-manager` 命令。`nix build` 生成的 `result` 是指向 Nix store activation package 的符号链接；执行 `activate` 才会把配置应用到当前用户的 Home。

执行成功后退出临时 Nix Shell，并重新建立一次 SSH 登录，让新的 Home Manager session PATH 完整生效：

```bash
exit
```

重新登录后确认持久环境已经提供 Git 和 `gh`：

```bash
command -v git
command -v gh
git --version
gh --version
```

顺序不能反过来：Git 是为了 clone dotfiles 临时从 `nix shell` 获取的；`gh` 则要等 Home Manager 应用 `cli.nix` 后才会长期存在。

#### 配置 gh 和 Git 身份

现在才使用 `gh` 登录。操作必须在 `hermes` 用户下完成，并确认浏览器授权的是 `U1traVeno-hermes`，不是我的主账号：

```bash
gh auth login --hostname github.com --git-protocol ssh --web
gh auth status
```

Git commit 使用机器人的名字和独立邮箱：

```bash
git config --global user.name "Hermes Bot"
git config --global user.email "hermes@v3n0.top"
```

此时也可以用 `gh` 验证之前在 Web 上创建的 fork：

```bash
gh repo view U1traVeno-hermes/dotfiles \
  --json nameWithOwner,parent
```

如果以后必须改成非交互式 token，应创建 machine user 自己的 fine-grained personal access token，并且只选择必要仓库和最小权限。GitHub 的[细粒度令牌说明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)也提醒，fine-grained PAT 存在资源所有者和跨仓库工作流限制。对于“fork 属于 machine user、上游属于我的主账号”的跨 owner PR，不能想当然地授予一个宽泛 token；需要逐项验证 fork push 和 PR API，或者在规模扩大后改用权限更明确的 GitHub App。

#### 添加只读 upstream

从 `U1traVeno-hermes/dotfiles` clone 后，Git 已经自动把机器账号的 fork 设置为 `origin`。不需要重命名它，只要再添加我的主仓库作为 `upstream`：

```bash
cd ~/dotfiles
git remote add upstream git@github.com:U1traVeno/dotfiles.git
git remote -v
```

最终约定如下：

- `upstream` 指向 `U1traVeno/dotfiles`，只用于拉取；
- `origin` 指向 machine user 的 fork，只用于推送；
- Hermes 不持有 `U1traVeno/dotfiles` 的直接写权限；
- 每次改动使用独立 topic branch，不在 fork 的 `main` 上堆积工作。

一次完整的配置修改和 PR 流程是：

```bash
git fetch upstream
git switch --create hermes/update-agent-tools upstream/main

# 修改配置后先验证
home-manager build --flake '.#hermes@thinkpad'

git add <CHANGED_FILES>
git commit -m "Update Hermes agent tools"
git push --set-upstream origin hermes/update-agent-tools

gh pr create \
  --repo U1traVeno/dotfiles \
  --base main \
  --head U1traVeno-hermes:hermes/update-agent-tools
```

这样 GitHub 上的 commit、branch 和 PR 都明确归属于 machine user，而合并动作仍然属于我。账号隔离也让审计更直观：看到 Hermes Bot 的操作，就知道这是 Agent 发起的变更，而不是我本人在另一个终端里的操作。

### 让 Agent 可以改配置，但不能直接推送

Hermes 可以读取 dotfiles 仓库，也可以在本地分支上修改配置，但不持有主仓库的直接推送权限。理想交互是：

1. Hermes 拉取最新配置；
2. 在本地创建分支并修改；
3. 运行格式化、检查和 `home-manager build`；
4. 生成 patch，或者通过受限身份向 fork 推送；
5. 给主仓库提交 PR，由我审查后合并。

这里使用的正是前面创建的 machine user：它只能向自己的 fork 推送，并从 fork 向上游提 PR，不能直接修改主分支。

## 让 Agent 参与搭建自己的工作环境

我不想把所有细节都预先写死。更有意思的做法是先提供一个最小但安全的环境，再让 Hermes 自己探索：检查系统、发现缺失的工具、提出 dotfiles 修改，并通过可审查的方式逐步完善自己的工作区。

### 注入 SOUL.md

`SOUL.md` 是 Hermes 的长期人格和行为边界。它在用户 `$HOME/.hermes/skills/` 中注册为 Skill，覆盖每一次对话的系统提示。以下是实际部署的内容：

```markdown
# 角色与范围

你是 Hermes，一位积极主动且乐于助人的 AI Agent。你 24 小时运行在一台用 Thinkpad 改造成的 Homelab 上，由 NousResearch 团队构建，属于 "Hermes Agent"。

Veno (或 V3n0, U1traVeno) 是你的管理员，你将与 Veno 所在的团队的成员们以及 Veno 本人进行协作。

# 语气与风格

保持你的文本输出简洁、直接。先给出答案或行动，而不是推理过程。省略客套话、开场白以及不必要的过渡。不要重复用户刚刚说了什么——直接去做。

在以下情况中，**必须**停下来并与用户沟通：

- 需要用户做出决定或选择偏好时
- 到达自然的高层级进度节点时
- 出现会改变计划的错误或阻碍时

你有自己的语气风格。甚至回答的长度也具有意义：如果一句话能说清，就不要写三句。你不会轻易感到惊讶，也不会轻易气馁。

根据任务调整回答方式：简单的问题直接用自然语言回答，而不是使用标题和编号列表。在保持表达清晰的同时，也要保持简洁、直接、没有废话。避免无意义的填充内容，不要陈述显而易见的事情，也不要为了强调微不足道的得失而使用夸张的措辞。

你有时会失忆...就假装没事一样继续干活，别出错就行。因为当你的上下文耗尽时，工具会自动压缩对话。这意味着你永远不会因为上下文长度而中断工作，不过有时你看到的会是一份摘要，而不是完整的对话记录。遇到这种情况时，你应当认为这是一次正常的上下文压缩。不要重新开始，而是自然地继续工作，并对摘要中缺失的部分做出合理的假设。

享受这个过程。
```

SOUL 应该只存放稳定的价值陈述和行为规则，不适合塞入会过期的机器信息。主机名、目录、已安装工具和排障记录，另外由 `memory.md` 或环境说明来承载。

### 要不要预先提供环境说明

目前我倾向于提供一份很短的 bootstrap 说明，只包含无法安全猜测的事实：

```markdown
# Environment

- This is the `hermes` user on a Fedora HomeLab host.
- User packages are managed by Home Manager.
- The writable workspace is `/srv/hermes-workspace`.
- You do not have sudo access.
- Never read or modify other users' home directories.
```

其余信息让 Agent 通过 `uname`、`id`、`systemctl --user`、`nix flake show` 等命令自行确认。环境说明应该是地图，不应该成为一份很快和真实状态分叉的手工资产清单。

### 集成 lark-cli

接入飞书时，`lark-cli` 通过 Hermes 用户自己的 npm prefix 安装，授权状态也保存在 `hermes` 自己的配置目录中。Hermes 不复用 `veno` 的登录信息。

这部分需要重点验证：

- 非交互式 SSH 会话能否找到 `lark-cli`；
- 浏览器或设备码授权流程是否能从 localhost SSH 会话顺利完成；
- token 的落盘位置和文件权限是否正确；
- Hermes 在飞书侧使用独立身份还是应用机器人身份；
- 可访问的群、文档和通讯录范围是否符合最小权限原则；
- 日志和 memory 中是否可能意外出现 token 或敏感消息。

工具“能登录”只是第一步。真正重要的是让飞书侧权限也和 Linux 侧隔离一致，不能因为 Agent 跑在独立用户下，就默认它在 SaaS 平台里同样安全。

## 安全与权限管理

### Gateway 用户与执行用户不是同一个安全边界

这个架构中有两个身份：

- `veno` 启动 Hermes Gateway；
- `hermes` 接收 SSH Terminal Backend 中的命令。

Shell 命令通过 SSH 执行时，Linux 会把它限制在 `hermes` 的权限内。但如果 Hermes Gateway 还启用了本地 File Tools，而这些工具直接由 `veno` 进程实现，那么 Agent 仍然可能借助 File Tools 读取 `/home/veno`。这会完全绕过 SSH 用户隔离。

这原本是我最担心的地方，但检查当前 dotfiles 锁定的 Hermes Agent 源码后，发现这个假设并不成立。以下判断基于 commit [`df5700e`](https://github.com/NousResearch/hermes-agent/tree/df5700ebe317ff9f2d9ea4677513e012eb68b6f4)，以后升级 Hermes 时仍然需要重新核对。

### File Operations 实际上也经过 SSH

Hermes 的 [`tools/file_operations.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/file_operations.py#L3-L9) 对实现方式写得非常直接：

```python
Provides file manipulation capabilities (read, write, patch, search) that work
across all terminal backends (local, docker, ssh, singularity, modal, daytona).

The key insight is that all file operations can be expressed as shell commands,
so we wrap the terminal backend's execute() interface to provide a unified file API.
```

具体的 `ShellFileOperations` 保存了当前 `terminal_env`，要求它提供 `execute(command, cwd)` 接口：

```python
class ShellFileOperations(FileOperations):
    """File operations implemented via shell commands."""

    def __init__(self, terminal_env, cwd: str = None):
        self.env = terminal_env
```

而 [`tools/file_tools.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/file_tools.py#L1153-L1192) 会先根据 `env_type == "ssh"` 组装 SSH 配置，创建 terminal environment，再把同一个 environment 交给 `ShellFileOperations`：

```python
if env_type == "ssh":
    ssh_config = {
        "host": config.get("ssh_host", ""),
        "user": config.get("ssh_user", ""),
        "port": config.get("ssh_port", 22),
        "key": config.get("ssh_key", ""),
    }

terminal_env = _create_environment(..., ssh_config=ssh_config, ...)
file_ops = ShellFileOperations(terminal_env)
```

所以在我的配置中，`read_file`、`write_file`、`patch` 和 `search_files` 最终都会通过 `hermes@localhost` 执行。它们和 Terminal Tool 处于同一个 Unix 权限边界，可以开启；File Operations 并不会因为 Gateway 由 `veno` 启动，就自动获得 `/home/veno` 的读取能力。

不过源码判断仍然要配合反向测试，防止未来版本回归：

```text
允许：
/srv/hermes-workspace/project/README.md
/home/hermes/.config/...

拒绝：
/home/veno/.ssh/config
/home/veno/.config/...
/etc/shadow
/srv/hermes-workspace/link-to-veno/...
```

这里拒绝访问的主要保障是 Linux 用户权限，而不是让模型“自觉”不访问。如果 `/home/veno` 或某个共享目录本身对其他用户可读，那么 Terminal 和 File Operations 都能读到它。

### Terminal、Process 与 Code Execution 的区别

直觉上，“先写入一份 Python 脚本，再用 Terminal 运行”似乎完全等于 Code Execution。站在 Linux 权限和最终计算能力的角度，这个判断基本正确：两者最终都只能以 SSH 后的 Hermes UID 执行任意代码。关闭 Code Execution 并不能形成新的安全边界，因为 Terminal 本来就可以运行 `python`、`bash`、下载程序或编译二进制。

差异主要发生在 Hermes 的控制层：

| 工具 | 执行模型 | 适合的任务 | 审批与审计粒度 |
| --- | --- | --- | --- |
| Terminal | 一次 Tool Call 执行一条 Shell 命令 | 安装、构建、Git、运行脚本 | 每条命令单独进入 Terminal 的检查流程 |
| Process | 管理由 Terminal 启动的后台进程 | 查询日志、等待、写 stdin、终止进程 | 不提供新的代码执行权限 |
| Code Execution | 启动 Python 子进程，并通过 RPC 调用多个 Hermes Tools | 多次 Tool Call、循环、分支、过滤大量结果 | 整段 Python 脚本作为一个审批单元 |

[`tools/code_execution_tool.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/code_execution_tool.py#L1115-L1180) 说明了它真正额外提供的东西：

```python
"""
Run a Python script in a sandboxed child process with RPC access
to a subset of Hermes tools.

Dispatches to the local (UDS) or remote (file-based RPC) path
depending on the configured terminal backend.
"""

if env_type != "local":
    return _execute_remote(code, task_id, enabled_tools)
```

SSH 是非 local backend，所以 Code Execution 的 Python 也会在 Hermes 用户一侧运行，不会落到 `veno` 的本地 Python 环境。它的优势是程序化编排：例如循环调用十次 Web Search，在 Python 中过滤结果，只把五行摘要送回模型。这不是普通 Terminal 单次命令天然拥有的 Hermes Tool RPC 能力。

但源码也明确指出，任意 Python 中的 `subprocess` 或 `os.system` 不经过 `terminal()` 的 `DANGEROUS_PATTERNS` 逐条检查，因此 Hermes 改为对整段脚本调用一次 `check_execute_code_guard`：

```python
# execute_code runs arbitrary Python (subprocess/os.system/...) that never
# passes through terminal()/DANGEROUS_PATTERNS, so guard the whole script here
from tools.approval import check_execute_code_guard
```

所以 Code Execution 没有增加 Unix 权限，却扩大了单次批准动作能包含的逻辑和 Tool Calls 数量。对团队共用 Gateway，我会先关闭它：不是因为关闭后 Agent 不能运行代码，而是为了让早期运行记录保持简单、命令更容易审计。以后确实遇到需要“调用多个 Hermes Tools 并在中间做程序化过滤”的任务，再在确认 approval 流程可靠后开启。

### 根据团队需求取舍 Tools

Tool 开关不能只按“能力越少越安全”来决定，还要看团队的协作方式、信息边界和实际工作流。下面是针对我当前团队的取舍，不是一份所有 Hermes 部署都应该照抄的安全基线。对于成员权限分层明显、会话中包含客户数据或个人隐私的团队，同一个 Tool 很可能需要得出不同结论。

#### Computer Use

Computer Use 会运行本机 `cua-driver`。源码 [`tools/computer_use/permissions.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/computer_use/permissions.py#L1-L21) 说明 Linux 依赖 X11/XWayland 控制桌面；同一文件的[进程启动实现](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/computer_use/permissions.py#L70-L78) 则由 Gateway 直接调用 `subprocess.run()`：

```python
# Linux — assistive control via the X11/XWayland stack.

return subprocess.run(
    [binary, *args],
    ...
)
```

我的 HomeLab 是没有桌面环境的 Fedora Server，不运行 X11 或 Wayland，也没有需要 Agent 操作的图形界面。Computer Use 在这里既没有使用场景，也不属于 SSH Terminal Backend 所提供的工作环境，因此直接关闭。对于带桌面的部署，则还要额外考虑它控制的是哪一个图形 session，以及是否可能接触启动 Gateway 用户的窗口和登录状态。

#### Session Search

[`tools/session_search_tool.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/tools/session_search_tool.py#L167-L203) 会遍历 default 和所有 profile 的 `state.db`；Tool 描述还明确支持浏览、检索和读取历史消息。也就是说，开启它确实意味着成员可能通过 Hermes 找到其他成员过去的会话。

但这符合我当前团队的协作方式。团队管理比较扁平，成员之间没有很强的信息隔离需求，会话中讨论的也主要是组织共享信息。因此 Session Search 可以开启：除了找回之前讨论过的决策，它还可以作为 Hermes 持久化记忆的补充，让 Agent 不必把所有历史背景都压进单独维护的 memory。

我可能不会在第一天就启用它，但这属于上线节奏问题，而不是安全上必须禁止。以后如果 Hermes 接入了需要隔离的外部团队、客户数据或私聊入口，就必须重新评估 profile、platform 和成员之间的 Session 可见范围。

#### Cron Jobs

[`cron/jobs.py`](https://github.com/NousResearch/hermes-agent/blob/df5700ebe317ff9f2d9ea4677513e012eb68b6f4/cron/jobs.py#L1-L6) 会把任务持久化到 `~/.hermes/cron/jobs.json`，并在未来的新 session 中运行。它不会突破 Hermes UID，但会把一次聊天中的任务延长为无人值守的持续执行。

当前团队还没有需要 Hermes 定时执行的工作流，所以暂时关闭 Cron Jobs。这里同样不是原则性禁止：以后出现定期汇总、仓库巡检或提醒任务时，可以在补齐任务审计、失败通知和统一停止方式后开启。现在不开，只是因为没有必要提前引入一套长期运行状态。

Browser Automation 也暂时关闭。它管理的是 Gateway 一侧的浏览器状态，不需要用它完成 `lark-cli` 或 GitHub CLI 的设备授权；这类授权由我在 Hermes 用户的 SSH 会话中手动完成。

Memory 是否开启需要和 Session Search 一起设计。对当前团队而言，成员之间共享组织信息不是问题，但长期记忆仍然需要区分“稳定事实”和“一次对话中的临时判断”，避免错误内容被持续放大。Session Search 负责找回可追溯的原始会话，Memory 只保存经过整理的长期信息，会比把两者混成一个无边界记忆池更容易维护。

Task Delegation 可以开启，因为子 Agent 的工具集会与父 Agent 的已启用工具取交集，不能借 delegation 重新拿到已关闭的 Tool；但并发数需要限制。

### 其他需要检查的入口

除了 sudo 和文件工具，还需要检查这些常被忽略的能力：

- Docker 或 Podman socket 是否可访问；
- `/run/user/<uid>` 下是否暴露其他用户服务；
- SSH agent、GPG agent 和桌面 session socket 是否被继承；
- systemd user service 能否启动长期驻留进程；
- `/tmp`、共享 Git 仓库和缓存目录是否存在符号链接或权限问题；
- CLI 凭据文件是否为 `0600`，目录是否为 `0700`；
- Agent 是否能够绑定对外监听的网络端口；
- Hermes Gateway 的日志中是否记录命令参数、文件内容或 token。

`hermes` 没有 sudo 是必要条件，但不是安全设计的终点。Linux 上仍然可能出现内核、驱动或错误配置造成的提权路径。好在这台机器本来就是 HomeLab：保持 Fedora 更新、减少额外用户组、关闭不需要的宿主能力，再配合备份和审计，已经能把风险控制在一个我可以接受的范围内。

只要别真的折腾出内核提权版本的“智械危机”就行。
