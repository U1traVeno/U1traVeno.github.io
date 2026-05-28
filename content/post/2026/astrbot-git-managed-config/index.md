---
title: "从零开始搭建一个 Git 管理的 AstrBot 配置仓库"
description: "记录把 AstrBot 的运行配置、插件和 Skills 拆成独立 Git 仓库，并先用 Docker Compose 跑通最小实例的过程。"
date: 2026-05-28T17:21:56+08:00
image:
math:
license:
hidden: false
comments: true
draft: false
tags: ['AstrBot', 'Docker Compose', 'GitOps', 'Workflow']
---

最近想把 AstrBot 当成一个长期可维护的团队机器人入口：后续它要接飞书、Gitea、沙箱、`lark-cli`、`tea`、自定义插件和 Skills。如果这些东西都只堆在某台机器的 `data/` 目录里，迟早会变成不可复现的手工状态。

所以第一步不是立刻做复杂自动化，而是先从 0 开始做一个可以被 Git 管理的 AstrBot 配置项目。本文先记录最小版本：创建独立仓库，用 Docker Compose 跑通 AstrBot WebUI，并明确哪些文件应该进 Git，哪些运行态文件应该忽略。

## 目标

我希望最终得到这样的结构：

```text
astrbot-config/
  compose.yml
  .env.example
  .gitignore
  README.md

  data/
    cmd_config.json
    mcp_server.json
    config/
    plugins/
    skills/

  ops/
```

这里的重点是：`data/` 不是整体入库，而是只把可复现、可审查的配置放进 Git。

应该进入 Git 的内容包括：

- `data/cmd_config.json`
- `data/config/`
- `data/plugins/`
- `data/skills/`
- `data/mcp_server.json`
- 自己维护的插件、Skills、配置模板

不应该进入 Git 的内容包括：

- `.env`
- `data/dist/`
- `data/dashboard.zip`
- `data/*.db`
- `data/knowledge_base/`
- `data/temp/`
- `data/workspaces/`
- `data/attachments/`
- `data/site-packages/`

## 初始化项目

新项目放在：

```bash
/home/veno/Projects/astrbot-config
```

先创建目录和 Git 仓库：

```bash
cd ~/Projects
mkdir astrbot-config
cd astrbot-config
git init
git branch -m main
```

目录骨架：

```bash
mkdir -p data/config data/plugins data/skills ops
touch data/.gitkeep \
  data/config/.gitkeep \
  data/plugins/.gitkeep \
  data/skills/.gitkeep \
  ops/.gitkeep
```

## Docker Compose

`compose.yml` 使用官方镜像：

```yaml
services:
  astrbot:
    image: ${ASTRBOT_IMAGE:-soulter/astrbot:latest}
    container_name: ${ASTRBOT_CONTAINER_NAME:-astrbot-config}
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "${ASTRBOT_WEB_PORT:-6185}:6185"
      - "${ASTRBOT_ONEBOT_PORT:-6199}:6199"
    environment:
      - TZ=${TZ:-Asia/Shanghai}
    volumes:
      - ./data:/AstrBot/data:z
      - /etc/localtime:/etc/localtime:ro
```

`.env.example`：

```dotenv
ASTRBOT_IMAGE=soulter/astrbot:latest
ASTRBOT_CONTAINER_NAME=astrbot-config
ASTRBOT_WEB_PORT=6185
ASTRBOT_ONEBOT_PORT=6199
TZ=Asia/Shanghai
```

实际运行时复制一份 `.env`，但 `.env` 不进 Git：

```bash
cp .env.example .env
```

## Git Ignore

`.gitignore` 的核心是排除运行态文件：

```gitignore
.env
*.log

data/dist/
data/temp/
data/attachments/
data/webchat/
data/site-packages/
data/knowledge_base/
data/workspaces/
data/plugin_data/
data/dashboard.zip
data/*.db
data/*.db-*
data/t2i_templates/

# Keep config-managed areas tracked.
!data/
!data/config/
!data/plugins/
!data/skills/
```

这样 AstrBot 首次启动时生成的一堆数据库、WebUI 静态资源、知识库文件不会污染配置仓库。

## 清掉旧实例

因为这是一个从 0 开始的新部署，所以旧 AstrBot 容器直接作废。

先查看容器：

```bash
docker ps -a --format '{{.ID}} {{.Names}} {{.Image}} {{.Ports}} {{.Status}}'
```

当时发现旧容器 `astrbot` 占用了 `6185`：

```text
astrbot soulter/astrbot:latest 0.0.0.0:6185->6185/tcp Up ...
```

移除旧 AstrBot：

```bash
docker rm -f astrbot
```

我没有动 `napcat`，因为它不是 AstrBot 本体。

## 启动新实例

启动：

```bash
docker compose up -d
```

第一次启动时踩到一个小坑：因为前一次端口冲突已经创建了容器，后续虽然配置正确，但实际端口没有发布出来。解决方式是强制重建：

```bash
docker compose up -d --force-recreate
```

查看状态：

```bash
docker ps --format '{{.Names}} {{.Ports}} {{.Status}}'
```

最终看到：

```text
astrbot-config 0.0.0.0:6185->6185/tcp, 0.0.0.0:6199->6199/tcp Up
```

日志里确认 WebUI ready：

```text
AstrBot v4.24.2 WebUI is ready
Local: http://localhost:6185
Default username/password: astrbot / astrbot
```

访问地址：

```text
http://localhost:6185
```

默认账号密码：

```text
astrbot / astrbot
```

## 处理生成的配置

AstrBot 会在 `data/` 下生成主配置：

```text
data/cmd_config.json
data/mcp_server.json
```

其中 `data/cmd_config.json` 里会出现运行时生成的 `dashboard.jwt_secret`。这个值不适合进 Git，所以提交前我把它清空：

```json
"dashboard": {
  "jwt_secret": ""
}
```

容器以 root 写入挂载目录时，本机用户可能无法直接修改文件。可以通过容器把 `/AstrBot/data` 的所有权改回来：

```bash
docker exec astrbot-config chown -R 1000:1000 /AstrBot/data
```

然后再清理 `cmd_config.json`。

## 初始提交

确认 Git 状态：

```bash
git status --short --ignored
```

应该只看到 `.env`、数据库、WebUI 静态资源等被忽略，配置文件和骨架目录可提交。

提交：

```bash
git add .env.example .gitignore README.md compose.yml \
  data/.gitkeep \
  data/config/.gitkeep \
  data/plugins/.gitkeep \
  data/skills/.gitkeep \
  data/cmd_config.json \
  data/mcp_server.json \
  ops/.gitkeep

git commit -m "chore: initialize astrbot docker config repo"
```

当前提交：

```text
8a4a00d chore: initialize astrbot docker config repo
```

## WebUI 初始配置

启动跑通之后，我在 AstrBot WebUI 里做了第一次人工配置：

- 修改了初始 Dashboard 用户名和密码
- 在模型提供商里创建了 DeepSeek API 来源
- 启用了 `deepseek/deepseek-v4-pro` 作为模型
- 新建了一个配置文件，展示名称为 `Feishu - Flow Project`
- 暂时还没有接入飞书机器人、沙箱、CLI、Skills 或插件

这些操作反映到仓库里后，`git status` 看到：

```text
 M data/cmd_config.json
?? data/config/abconf_99578339-b87b-41b4-97a9-5c4af491f6c2.json
?? data/skills.json
```

`data/cmd_config.json` 的主要变化是：

- `dashboard.username` 从 `astrbot` 改成了 `veno`
- `dashboard.password` 更新为新的密码哈希
- `dashboard.jwt_secret` 被运行时重新生成
- 新增 `provider_sources[0]`，来源 ID 为 `deepseek`
- 新增 `provider[0]`，模型 ID 为 `deepseek/deepseek-v4-pro`

其中 DeepSeek API key 目前由 AstrBot WebUI 直接写进了 `data/cmd_config.json`：

```json
{
  "provider_sources": [
    {
      "provider": "deepseek",
      "type": "openai_chat_completion",
      "api_base": "https://api.deepseek.com/v1",
      "id": "deepseek",
      "enable": true
    }
  ]
}
```

这里我最后选择了更朴素的方案：把这个仓库明确定位为私有配置仓库，并让 `data/cmd_config.json` 继续作为 AstrBot 运行时事实来源进入 Git。

原因是 AstrBot WebUI 会直接写这个 JSON，当前还不能确认它是否稳定支持从 `.env` 或模板安全回填 provider key、Dashboard 密码哈希和 `jwt_secret`。如果强行做模板渲染，反而可能引入“配置看起来可复现，但实际启动时被覆盖或漏注入”的风险。

因此现阶段的安全边界是：

- 私有 Git 仓库可以包含真实运行配置
- 不配置公开 remote，不把配置 diff 贴到公开聊天或博客里
- 如果未来要公开仓库，先轮换 provider key 和 Dashboard 凭据，再清理 Git 历史
- 真要提高 secret 安全等级时，再引入 SOPS 或 git-crypt，而不是先做脆弱的自动回填

另外，新建的配置文件实际落在：

```text
data/config/abconf_99578339-b87b-41b4-97a9-5c4af491f6c2.json
```

这个 JSON 文件本身没有直接写入 `Feishu - Flow Project` 字符串。也就是说，AstrBot 对“配置文件展示名”和 `abconf_*.json` 文件之间的映射，可能不完全靠这个 JSON 文件表达。后续如果要做严格 GitOps，需要继续确认配置文件命名和展示名的持久化位置。

## 私有配置提交

确认采用私有仓库策略后，我把 WebUI 产生的真实配置提交进 Git：

```text
e75b5fd chore: track astrbot webui config privately
```

这次提交包含：

- `data/cmd_config.json`：Dashboard 用户、DeepSeek 来源和启用模型等真实运行配置
- `data/config/abconf_99578339-b87b-41b4-97a9-5c4af491f6c2.json`：WebUI 新建配置文件对应的 JSON
- `data/skills.json`：当前为空的 Skills 注册状态
- `README.md`：补充私有仓库安全边界说明

提交后工作区是干净的，并且当前没有配置 Git remote。

## Shipyard Neo 沙箱与 Feishu CLI

下一步我按 AstrBot 文档接入沙箱能力。文档里的关键点是：`Computer Use Runtime` 可以设为 `sandbox`，沙箱驱动选择 `Shipyard Neo`；Bay 默认监听 `8114`，AstrBot 通过 `Shipyard Neo API Endpoint` 和 `Shipyard Neo Access Token` 连接。

这次采用本机独立 Shipyard Neo 部署，而不是把 Bay 塞进 AstrBot 容器：

- Shipyard Neo 部署目录：`/home/veno/Projects/shipyard-neo-deploy`
- Bay endpoint：`http://bay:8114`，供 AstrBot 通过 Docker 网络访问
- AstrBot `computer_use_runtime`：`sandbox`
- AstrBot `sandbox.booter`：`shipyard_neo`
- AstrBot `shipyard_neo_profile`：`python-default`
- Bay token：按文档写入 `shipyard_neo_access_token`，继续由私有配置仓库管理

Fedora 上还遇到一个实际问题：Bay 需要访问 Docker socket 来创建 sandbox 容器，但 SELinux 会拦截默认 bind mount。由于 Bay 挂 Docker socket 本身就已经是高权限组件，我在 Bay service 上显式加了：

```yaml
security_opt:
  - label:disable
```

这不是为了让普通业务容器放宽隔离，而是为了让 Bay 这个 Docker 控制面组件在 Fedora 上能按设计工作。

Feishu CLI 和 Skills 按 `larksuite/cli` 官方仓库处理：

- 本机先执行官方推荐的 `npx skills add larksuite/cli -g -y`，安装官方 lark skills
- AstrBot 仓库中同步了官方安装器发现的 26 个 lark skills 到 `data/skills/`
- 自定义 Shipyard Neo ship 镜像继承 `ghcr.io/astrbotdevs/shipyard-neo-ship:latest`
- 镜像内执行官方推荐的 `npx /cli install` 安装 `lark-cli`
- 额外加入本机已有的静态 `tea` 二进制

最终验证：Bay 能创建 `python-default` sandbox，并且在真实 sandbox 内执行：

```bash
lark-cli --version && tea --version
```

返回 `lark-cli version 1.0.42` 和 `tea 0.12.0`。

## CLI 授权状态持久化计划

安装 `lark-cli` 和 `tea` 之后，还有一个更实际的问题：Agent 每次要用飞书或 Gitea 能力时，不应该重新思考“去哪登录、token 放哪、下次还在不在”。这件事不能交给 Skill 本身解决。Skill 只应该描述工具怎么用，真正的权限边界仍然应该在飞书应用权限、用户授权、Gitea token scope 和 sandbox 运行时配置上。

这次先采用一个保守部署计划：

- 镜像层只安装工具：`lark-cli`、`tea` 和对应 Skills
- Skill 层只提供调用说明，不写入任何 token
- Shipyard Neo profile 把 `HOME` 和 `XDG_CONFIG_HOME` 指到 `/workspace`
- CLI 登录态和配置落在 `/workspace/.config`，由 Shipyard Neo Cargo 持久化

这样在同一个 AstrBot 消息会话复用的 Neo sandbox 中，Agent 使用 `lark-cli` 或 `tea` 时只需要做轻量验证，例如 `lark-cli config show`、`tea whoami`，不需要每次重新设计授权流程。

当前部署计划修改 `python-default` profile：

```yaml
env:
  HOME: "/workspace"
  XDG_CONFIG_HOME: "/workspace/.config"
```

这不是把密钥写进镜像，也不是把密钥写进 Skill，而是把两个 CLI 的默认配置目录稳定放进 sandbox workspace。后续如果要跨 sandbox 生命周期、跨 AstrBot 配置文件隔离账号，就需要进一步引入固定 external cargo、按 profile 区分配置目录，或让 AstrBot 在创建 sandbox 时把当前配置文件 ID 传给 Shipyard Neo。

部署验证通过后，真实 Neo sandbox 中的结果是：

```text
XDG_CONFIG_HOME=/workspace/.config
HOME=/workspace
lark-cli version 1.0.42
tea 0.12.0
```

随后我重启了 AstrBot，让旧的 sandbox booter 缓存失效。后续 Agent 进入新的 sandbox 时，会默认把 `lark-cli` 和 `tea` 的配置写入 `/workspace/.config`。这意味着常规使用时不需要每次重新判断授权目录；只要当前 sandbox 的 Cargo 还在，CLI 就能复用已有登录态。

这里仍然有一个边界：AstrBot 当前创建 Shipyard Neo sandbox 时只传 `profile` 和 `ttl`，没有把当前 AstrBot 配置文件 ID 传给 Bay，也没有指定固定 external cargo。因此这个方案解决的是“同一 sandbox/Cargo 内的授权复用”，不是“任意 sandbox 销毁后永久复用同一账号”。如果要把账号状态做成长期、可分组的基础设施，需要继续扩展 profile 或 AstrBot 的 sandbox 创建参数。

## 不同配置文件使用不同账号

接下来还有一个更重要的设计问题：如果不同 AstrBot 配置文件要使用不同的 Gitea 账号和飞书账号，账号状态应该绑在哪里？

当前 AstrBot 配置文件可以各自设置 `shipyard_neo_profile`，所以短期可以做多个 Shipyard Neo profile，例如 `python-default`、`python-feishu-flow`、`python-gitea-work`。每个 profile 用同一份工具镜像，但把 `HOME` / `XDG_CONFIG_HOME` 指向自己的目录约定。这样同一个 sandbox 内的 CLI 配置不会互相踩。

但这还不是最完整的方案。因为 AstrBot 现在没有把“当前配置文件 ID”或“目标账号组”传给 Bay，也没有指定 external cargo。只靠 profile，账号状态仍然跟当前 sandbox/Cargo 生命周期绑定。

更干净的长期方案是：

- 在 Shipyard Neo 中为每个账号组创建 external cargo
- 在 AstrBot 配置文件里增加或约定一个 `shipyard_neo_cargo_id`
- 创建 sandbox 时传入 `cargo_id`
- `lark-cli` 和 `tea` 继续把配置写到 `/workspace/.config`

这样账号状态就从“某个临时 sandbox 的副产物”变成“某个 AstrBot 配置文件绑定的持久化 workspace”。例如：

```text
default config       -> cargo-default       -> /workspace/.config
feishu-flow config   -> cargo-feishu-flow   -> /workspace/.config
gitea-work config    -> cargo-gitea-work    -> /workspace/.config
```

如果不想改 AstrBot，最稳妥的替代方案是为不同账号组拆成不同 AstrBot 实例：每个实例有自己的配置仓库、自己的 Bay profile 或 Bay 部署、自己的 CLI 登录态。这比较笨，但隔离边界清晰，出问题时也容易回滚。

## 当前结果

现在我有了一个新的、干净的 AstrBot 配置仓库：

```text
/home/veno/Projects/astrbot-config
```

它已经能通过 Docker Compose 启动 AstrBot，并且将运行态数据和可同步配置分开。

下一步再继续往这个仓库里加：

- Shipyard Neo 沙箱配置
- 内置 `lark-cli` 和 `tea` 的工具运行环境
- 用 Git 管理的全局 Skills
- 插件内置 Skills
- 自研 Gitea / 飞书同步插件
- 可同步的机器人记忆、规则和状态映射

第一阶段先到这里：先让 AstrBot 以一个可复现的 GitOps 形态跑起来。
