---
title: "给 Hugo Stack 首页添加可配置的分类与文章置顶"
description: "通过站点级首页模板，为 Hugo Stack 增加可排序的分类合集和单篇文章置顶配置。"
date: 2026-07-13T16:00:00+08:00
image:
math: false
license:
hidden: false
comments: true
draft: false
tags: ["Hugo", "Stack"]
---

Stack 提供了 categories 侧边栏组件，但它只会按照文章数量展示分类，并不负责把某个分类合集放到首页文章流上方。主题的首页模板也只是筛选普通文章、分页，然后逐篇渲染：

```go-html-template
{{ $pages := where .Site.RegularPages "Type" "in" .Site.Params.mainSections }}
{{ $pag := .Paginate $pages }}

{{ range $pag.Pages }}
    {{ partial "article-list/default" . }}
{{ end }}
```

因此，这个功能需要覆盖主题的首页模板。覆盖文件放在站点自己的 `layouts/index.html`，而不是修改 `themes/hugo-theme-stack`，这样更新主题子模块时不会丢失改动。

## 统一配置分类和文章

我在 `hugo.toml` 中使用一个有序的 `items` 数组。数组顺序就是首页显示顺序，目前置顶的是 Paramer 开发记录合集：

```toml
[params.homepage.pinned]
enabled = true
categoryArticleLimit = 3

[[params.homepage.pinned.items]]
type = "category"
value = "Paramer 开发记录"
```

需要置顶单篇文章时，继续添加一个条目即可。`value` 是 Hugo 中的内容路径，`label` 可以省略；省略后使用文章原始标题：

```toml
[[params.homepage.pinned.items]]
type = "article"
value = "/post/2026/chezmoi/"
label = "可选的自定义标题"
```

两种类型放在同一个数组里，比 `pinnedCategories` 和 `pinnedArticles` 两个独立列表更容易控制混合排序，以后也能继续扩展新的置顶类型。

## 解析分类合集

分类的配置值是显示名称，例如 `Paramer 开发记录`。Hugo 的 taxonomy map 使用小写分类名作为 key，而分类页面 URL 使用 `urlize` 后的 slug，两者不能混用：

```go-html-template
{{ $termKey := lower $item.value }}
{{ $termSlug := lower ($item.value | urlize) }}
{{ $termPages := index .Site.Taxonomies.categories $termKey }}

<a href="{{ printf "/categories/%s/" $termSlug | relURL }}">
    {{ $item.value }}
</a>
```

拿到 taxonomy 中的页面集合后，过滤隐藏文章、按日期倒序，再按照 `categoryArticleLimit` 截取即可。单篇文章则可以直接用 `.Site.GetPage $item.value` 解析。

如果配置指向不存在的分类或文章，模板会通过 `warnf` 在构建日志中报告错误，而不是生成一个失效链接。

## 不改变原有文章流

置顶区块只在分页第一页显示：

```go-html-template
{{ if eq $pag.PageNumber 1 }}
    {{ partial "homepage/pinned.html" . }}
{{ end }}
```

置顶内容仍然保留在下面的正常时间线中。这样置顶只影响首页的信息层级，不会改变 Hugo 的分页集合，也不会让某篇文章因为被置顶而从归档或 RSS 中消失。

相关实现分别位于：

- `layouts/index.html`：覆盖 Stack 首页，在第一页插入置顶区块；
- `layouts/partials/homepage/pinned.html`：解析和渲染分类、文章条目；
- `assets/scss/custom.scss`：响应式布局和卡片样式；
- `hugo.toml`：站点级置顶配置。
