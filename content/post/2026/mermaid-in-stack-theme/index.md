---
title: "Hugo Stack 主题添加 Mermaid 支持"
description: 
date: 2026-01-24T21:46:07+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: false
links:
    - title: Hugo
      website: https://gohugo.io/
      image: apple-touch-icon.png
    - title: Hugo Theme - Stack
      website: https://stack.jimmycai.com/
      image: stack-logo.png
---

参考:

[Hugo docs - Diagrams - Mermaid diagrams](https://gohugo.io/content-management/diagrams/#mermaid-diagrams)

[Stack docs - Custom Header / Footer](https://stack.jimmycai.com/config/header-footer)

[feat: add support for Mermaid diagrams in Markdown content #1186](https://github.com/CaiJimmy/hugo-theme-stack/pull/1186)

在 `layouts` 添加如下两个文件:

```html
<!-- layouts/_markup/render-codeblock-mermaid.html -->
<pre class="mermaid">
  {{ .Inner | htmlEscape | safeHTML }}
</pre>
{{ .Page.Store.Set "hasMermaid" true }}
```

```html
<!-- layouts/partials/head/custom.html -->
{{ if .Store.Get "hasMermaid" }}
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: true,
      theme: 'neutral',
    });
  </script>
{{ end }}
```

在黑暗模式下显示比较有问题, 我没有折腾比较好的解决方案
