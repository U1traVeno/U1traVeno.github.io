# Veno's blog

Veno 的博客。

使用 Stack 主题，giscus 评论。

## 本地部署

1. clone
2. 安装 hugo
3. `git submodule update --init --recursive`
4. `hugo server` 或 `hugo server -D`

## 友链

### 怎么申请

1. 先在你的站点添加本站的链接（信息见下方）。
2. 打开[友链申请表](https://github.com/U1traVeno/U1traVeno.github.io/issues/new?template=friend-link.yml)（需要 GitHub 账号），按提示填写并提交。
3. 机器人会在一分钟内回复：
   - 检查未通过：评论里会写明原因，直接编辑你的 Issue，保存后会自动重新检查。
   - 检查通过：自动生成 PR，我确认后合并，合并后几分钟内上线，Issue 会自动关闭。

要修改（换头像、改简介、换域名）或撤下友链，使用同一个表单，在“类型”里选对应项，“站点地址”填写现有友链使用的地址。

### 收录标准

- 个人博客或个人站点，以原创内容为主。
- 站点能正常访问，并已添加本站的互链。
- 不收录违法、色情、商业推广类站点，也不收录长期没有内容更新的站点。
- 站长保留最终是否收录的决定权，也可以之后撤下。

### 本站信息

- 名称：Veno's Blog
- 地址：https://v3n0.com/
- 头像：https://github.com/U1traVeno.png
- 简介：Worse is better.

### 机器人检查什么

站点地址和头像可访问（头像必须是图片，不超过 2 MB）、地址为 `https://`、名称不超过 50 字、简介不超过 40 字、没有重复条目。

### 维护者须知

- 友链数据在 `content/page/blogroll/index.md` 的 `links:`，由 `scripts/friend_link.py` 追加、修改、删除；测试：`cd scripts && python3 -m unittest`。
- 工作流 `.github/workflows/friend-link.yaml` 只处理带 `friend-link` 标签的 Issue（表单会自动加）。
- 仓库需要：标签 `friend-link`；Settings → Actions → General → Workflow permissions 里勾选 “Allow GitHub Actions to create and approve pull requests”。
