---
date: '2025-07-31T23:29:54+08:00'
draft: false
title: '使用 uv workspace 搭建 Python Monorepo'
tags: ['Python','uv']
comments: true
---

~~紫外线用 uv 很合理吧(x~~

有时候我们想在同一个仓库中维护多个Python项目，并且保证他们的依赖关系。这种代码组织策略叫 [**Monorepo**](https://zh.wikipedia.org/wiki/Monorepo), 这样更方便代码的重复利用，并且可以实现多个项目需要同时进行更改时的原子化提交，更便于团队协作 (~~尤其是当团队只有你一个人的时候~~)。

pip + pyproject.toml 不可能实现声明式的 Monorepo 搭建。不过2025年了，大多数人都更喜欢用 uv, poetry, pdm 之类的现代Python包和项目管理器。我倾向于使用uv。

uv 提供了 `workspace` 功能，和 Rust 的 Cargo 十分相似，因为 uv 本身就很受 Cargo 启发。通过这个功能，我们可以声明式地在 Pyproject.toml 中定义上面所说的 Monorepo ，我认为大多数时候已经足够好用。

uv 关于 workspace 的文档中有一个例子，但只给出了 pyproject.toml 的内容。其实大多数时候我们是不用手动编辑 pyproject.toml 中关于 `[tool.uv]` 的内容的，因为默认情况下，在现有包内运行 `uv init` 将将新创建的成员添加到工作区，如果工作区根目录中不存在 `[tool.uv.workspace]` 表格，则会创建一个。下面展示仅使用 uv 指令实现官方文档示例的仓库框架的搭建。

信天翁和喂鸟器都需要 seeds，信天翁需要喂鸟器。我这里做个小修改，seeds 仍是工作区成员，seeds 同时还需要支持在泥土中执行发芽操作，因此它依赖 dirt 库。

```shell
❯ pwd
/home/veno/Projects/uv_playground

❯ uv init --package albatross
Initialized project `albatross` at `/home/veno/Projects/uv_playground/albatross`

❯ cd albatross

❯ uv venv
Using CPython 3.13.5 interpreter at: /usr/bin/python3.13
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

❯ uv init --package bird-feeder
Adding `bird-feeder` as member of workspace `/home/veno/Projects/uv_playground/albatross`
Initialized project `bird-feeder` at `/home/veno/Projects/uv_playground/albatross/bird-feeder`

❯ rm bird-feeder -rf

❯ uv init --package packages/bird-feeder
Adding `bird-feeder` as member of workspace `/home/veno/Projects/uv_playground/albatross`
Initialized project `bird-feeder` at `/home/veno/Projects/uv_playground/albatross/packages/bird-feeder`

❯ uv init --package packages/seeds
Adding `seeds` as member of workspace `/home/veno/Projects/uv_playground/albatross`
Initialized project `seeds` at `/home/veno/Projects/uv_playground/albatross/packages/seeds`

❯ uv add tqdm
Resolved 5 packages in 308ms
      Built albatross @ file:///home/veno/Projects/uv_playground/albatross
Prepared 2 packages in 167ms
Installed 2 packages in 2ms
 + albatross==0.1.0 (from file:///home/veno/Projects/uv_playground/albatross)
 + tqdm==4.67.1

❯ uv add bird-feeder
Resolved 5 packages in 5ms
      Built albatross @ file:///home/veno/Projects/uv_playground/albatross
      Built bird-feeder @ file:///home/veno/Projects/uv_playground/albatross/packages/bird-feeder
Prepared 2 packages in 5ms
Uninstalled 1 package in 0.60ms
Installed 2 packages in 3ms
 ~ albatross==0.1.0 (from file:///home/veno/Projects/uv_playground/albatross)
 + bird-feeder==0.1.0 (from file:///home/veno/Projects/uv_playground/albatross/packages/bird-feeder)

❯ uv init --lib libs/dirt
Adding `dirt` as member of workspace `/home/veno/Projects/uv_playground/albatross`
Initialized project `dirt` at `/home/veno/Projects/uv_playground/albatross/libs/dirt`

❯ uv add dirt --package seeds
Resolved 6 packages in 194ms
      Built seeds @ file:///home/veno/Projects/uv_playground/albatross/packages/seeds
      Built dirt @ file:///home/veno/Projects/uv_playground/albatross/libs/dirt
Prepared 2 packages in 8ms
Installed 2 packages in 2ms
 + dirt==0.1.0 (from file:///home/veno/Projects/uv_playground/albatross/libs/dirt)
 + seeds==0.1.0 (from file:///home/veno/Projects/uv_playground/albatross/packages/seeds)

❯ tree .
.
├── libs
│   └── dirt
│       ├── pyproject.toml
│       ├── README.md
│       └── src
│           └── dirt
│               ├── __init__.py
│               └── py.typed
├── packages
│   ├── bird-feeder
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src
│   │       └── bird_feeder
│   │           └── __init__.py
│   └── seeds
│       ├── pyproject.toml
│       ├── README.md
│       └── src
│           └── seeds
│               └── __init__.py
├── pyproject.toml
├── README.md
├── src
│   └── albatross
│       └── __init__.py
└── uv.lock

14 directories, 14 files
```

pyproject.toml 中的内容较多，这里就不贴了，读者可以自己在电脑上试一下便知。

如果希望工作区不包含 seeds , 则需要在根项目，也就是`albatross`包的pyproject.toml中编辑 `[tool.uv.workspace]`, 添加`exclude = ["packages/seeds"]`。

> Every workspace needs a root, which is also a workspace member. In the above example, `albatross` is the workspace root, and the workspace members include all projects under the packages directory, except `seeds`.

这里 uv 的官方文档给出的例子是 Monorepo 中有一个根项目和几个辅助库。由于每一个工作区都需要一个根，如果我们想创建的 Monorepo 中，各个项目之间的地位是等价的，那么我们需要注意的是我们仍然需要先初始化整个 Monorepo 的根。

```shell
# 首先初始化根项目
❯ uv init --bare  # 使用--bare参数，仅生成一个pyproject.toml文件
Initialized project `monorepo`

❯ uv init --package packages/pkg_a
Adding `pkg-a` as member of workspace `/home/veno/Projects/uv_playground/monorepo`
Initialized project `pkg-a` at `/home/veno/Projects/uv_playground/monorepo/packages/pkg_a`

❯ uv init --package packages/pkg_b
Adding `pkg-b` as member of workspace `/home/veno/Projects/uv_playground/monorepo`
Initialized project `pkg-b` at `/home/veno/Projects/uv_playground/monorepo/packages/pkg_b`

❯ cat ./pyproject.toml
[project]
name = "monorepo"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[tool.uv.workspace]
members = [
    "packages/pkg_a",
    "packages/pkg_b",
]

❯ tree .
.
├── packages
│   ├── pkg_a
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src
│   │       └── pkg_a
│   │           └── __init__.py
│   └── pkg_b
│       ├── pyproject.toml
│       ├── README.md
│       └── src
│           └── pkg_b
│               └── __init__.py
└── pyproject.toml

8 directories, 7 files

```

附：

[UV Documentation - Using workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
