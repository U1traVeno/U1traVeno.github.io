#!/usr/bin/env python3
"""Apply a friend-link Issue Form submission to the blogroll page.

Reads the issue from the environment (ISSUE_BODY, ISSUE_NUMBER, ISSUE_AUTHOR),
validates it, edits the `links:` list in content/page/blogroll/index.md in
place, and writes the PR text / failure comment for the workflow to post.

Only the standard library is used. Values are always written as double-quoted
scalars, so nothing an applicant types can change the YAML structure.
"""
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BLOGROLL = Path("content/page/blogroll/index.md")
FIELDS = ("title", "description", "website", "image")
DESC_MAX = 40
TITLE_MAX = 50
UA = "Mozilla/5.0 (compatible; friend-link-check; +https://v3n0.com)"

SECTIONS = {
    "类型": "action",
    "站点名称": "title",
    "站点地址": "website",
    "头像": "image",
    "一句话简介": "description",
    "新地址": "new_website",
    "确认": "confirm",
}
ACTIONS = {"新增": "add", "修改": "update", "删除": "remove"}
ACTION_LABEL = {"add": "新增", "update": "修改", "remove": "删除"}


class FormatError(Exception):
    """The blogroll file has a shape this script does not handle."""


# --- issue parsing ---------------------------------------------------------


def parse_issue(body):
    body = body.replace("\r\n", "\n")
    out = {}
    for m in re.finditer(r"^### (.+?)[ \t]*\n(.*?)(?=^### |\Z)", body, re.M | re.S):
        label, value = m.group(1), m.group(2).strip()
        for prefix, key in SECTIONS.items():
            if label.startswith(prefix):
                out[key] = "" if value == "_No response_" else value
    return out


def checked(confirm, needle):
    return any(
        re.match(r"-\s*\[[xX]\]", line.strip()) and needle in line
        for line in confirm.splitlines()
    )


# --- blogroll file ---------------------------------------------------------


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except ValueError:
            return raw[1:-1]
    if raw.startswith("'"):
        return raw[1:-1].replace("''", "'")
    return raw


def links_bounds(lines):
    if not lines or lines[0].strip() != "---":
        raise FormatError("front matter not found")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise FormatError("front matter is not closed")
    start = next((i for i in range(1, end) if re.match(r"links:\s*$", lines[i])), None)
    if start is None:
        raise FormatError("`links:` not found in front matter")
    stop = next(
        (
            i
            for i in range(start + 1, end)
            if lines[i].strip() and not lines[i][0].isspace()
        ),
        end,
    )
    return start + 1, stop


def parse_entries(lines):
    """Return (entries, first, stop). Each entry has start/end (end exclusive,
    trailing blank lines excluded), its known fields and unknown raw lines."""
    first, stop = links_bounds(lines)
    starts = [i for i in range(first, stop) if re.match(r"  - \S", lines[i])]
    entries = []
    for n, s in enumerate(starts):
        limit = starts[n + 1] if n + 1 < len(starts) else stop
        e = limit
        while e > s + 1 and not lines[e - 1].strip():
            e -= 1
        entry = {"start": s, "end": e, "extra": []}
        for i in range(s, e):
            m = re.match(r"(?:  - |    )([A-Za-z_]\w*):(?:\s+(.*))?$", lines[i].rstrip())
            if not m:
                raise FormatError(f"unsupported line in links entry: {lines[i]!r}")
            key, raw = m.group(1), m.group(2) or ""
            if key in FIELDS:
                entry[key] = parse_value(raw)
            else:
                entry["extra"].append(lines[i].rstrip())
        if not entry.get("website"):
            raise FormatError(f"links entry at line {s + 1} has no website")
        entries.append(entry)
    return entries, first, stop


def render_entry(entry):
    out = []
    for key in FIELDS:
        value = entry.get(key)
        if value:
            prefix = "  - " if not out else "    "
            out.append(f"{prefix}{key}: {json.dumps(value, ensure_ascii=False)}")
    out.extend(entry["extra"])
    return out


def norm_url(url):
    p = urllib.parse.urlsplit(url.strip())
    host = (p.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    port = f":{p.port}" if p.port else ""
    query = f"?{p.query}" if p.query else ""
    return f"{host}{port}{p.path.rstrip('/')}{query}"


def find_entry(entries, website):
    key = norm_url(website)
    return next((e for e in entries if norm_url(e["website"]) == key), None)


def apply_edit(lines, action, fields):
    """Return the new lines. `fields` are already validated."""
    entries, first, stop = parse_entries(lines)
    target = find_entry(entries, fields["website"])
    lines = list(lines)
    if action == "add":
        new = render_entry({**fields, "extra": []})
        at = entries[-1]["end"] if entries else first
        lines[at:at] = [""] + new
    elif action == "update":
        merged = {k: target.get(k, "") for k in FIELDS}
        for key in FIELDS:
            if fields.get(key):
                merged[key] = fields[key]
        if fields.get("new_website"):
            merged["website"] = fields["new_website"]
        merged["extra"] = target["extra"]
        lines[target["start"] : target["end"]] = render_entry(merged)
    elif action == "remove":
        i = entries.index(target)
        if i + 1 < len(entries):
            lines[target["start"] : entries[i + 1]["start"]] = []
        else:
            begin = target["start"]
            while begin > first and not lines[begin - 1].strip():
                begin -= 1
            lines[begin : target["end"]] = []
    return lines


# --- validation ------------------------------------------------------------


def check_text(label, value, limit, errors):
    if len(value) > limit:
        errors.append(f"{label}过长（{len(value)} 字，上限 {limit}）")
    elif re.search(r"[\x00-\x1f\x7f]", value):
        errors.append(f"{label}不能包含换行或控制字符")


def check_url(label, value, errors):
    if re.search(r"\s", value) or len(value) > 2048:
        errors.append(f"{label}不是合法的 URL")
        return False
    p = urllib.parse.urlsplit(value)
    if p.scheme != "https" or not p.hostname:
        errors.append(f"{label}必须是以 https:// 开头的完整地址")
        return False
    return True


def assert_public(url):
    host = urllib.parse.urlsplit(url).hostname
    for info in socket.getaddrinfo(host, None):
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError("地址指向内网")


class PublicOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        assert_public(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def looks_like_image(head):
    return (
        head.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"\x00\x00\x01\x00"))
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
        or b"<svg" in head
        or head[4:12] in (b"ftypavif", b"ftypavis")
    )


def probe(url, want_image):
    """Return an error string, or None when the URL looks fine."""
    try:
        assert_public(url)
        opener = urllib.request.build_opener(PublicOnlyRedirect)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with opener.open(req, timeout=15) as r:
            if not want_image:
                return None
            size = int(r.headers.get("Content-Length") or 0)
            if size > 2 * 1024 * 1024:
                return f"文件过大（{size // 1024} KB，上限 2048 KB）"
            ctype = r.headers.get_content_type()
            if not (ctype.startswith("image/") or looks_like_image(r.read(512))):
                return f"返回的不是图片（Content-Type: {ctype}）"
    except urllib.error.HTTPError as e:
        if not want_image and e.code in (403, 429):
            return None  # likely bot protection; the owner will look at it
        return f"无法访问（HTTP {e.code}）"
    except (urllib.error.URLError, OSError, ValueError) as e:
        return f"无法访问（{getattr(e, 'reason', e)}）"
    return None


def validate(form, entries, network=True):
    errors = []
    action = next((v for k, v in ACTIONS.items() if form.get("action", "").startswith(k)), None)
    if not action:
        return None, ["未选择有效的类型"]
    fields = {k: form.get(k, "") for k in (*FIELDS, "new_website")}

    if not check_url("站点地址", fields["website"], errors):
        return action, errors
    target = find_entry(entries, fields["website"])

    if action == "add":
        if target:
            errors.append("该站点已经在友链里了；如需变更请选择“修改”")
        for key, label in (("title", "站点名称"), ("image", "头像 URL")):
            if not fields[key]:
                errors.append(f"{label}不能为空")
        if not checked(form.get("confirm", ""), "linked back"):
            errors.append("新增友链需要先在你的站点添加本站链接，并勾选对应确认项")
    else:
        if not target:
            errors.append("现有友链里找不到这个站点地址，请填写友链当前使用的地址")
        if action == "remove":
            return action, errors

    if not checked(form.get("confirm", ""), "README"):
        errors.append("请确认站点符合 README 里的收录标准")
    if fields["title"]:
        check_text("站点名称", fields["title"], TITLE_MAX, errors)
    if fields["description"]:
        check_text("简介", fields["description"], DESC_MAX, errors)
    if fields["new_website"]:
        if action != "update":
            errors.append("“新地址”只在修改时使用")
        elif check_url("新地址", fields["new_website"], errors):
            clash = find_entry(entries, fields["new_website"])
            if clash and clash is not target:
                errors.append("新地址已经被另一条友链使用")
    if fields["image"]:
        check_url("头像 URL", fields["image"], errors)

    if action == "update" and not any(
        fields[k] for k in ("title", "description", "image", "new_website")
    ):
        errors.append("没有填写任何要修改的内容")

    if network and not errors:
        for label, url, want_image in (
            ("站点地址", fields["new_website"] or fields["website"], False),
            ("头像 URL", fields["image"], True),
        ):
            if url:
                problem = probe(url, want_image)
                if problem:
                    errors.append(f"{label} {problem}：{url}")
    return action, errors


# --- driver ----------------------------------------------------------------


def pr_text(action, fields, number, author):
    shown = {
        "站点名称": fields["title"],
        "站点地址": fields["new_website"] or fields["website"],
        "头像": fields["image"],
        "简介": fields["description"],
    }
    rows = "\n".join(f"- {k}：{v}" for k, v in shown.items() if v)
    title = fields["title"] or fields["website"]
    pr_title = f"友链：{ACTION_LABEL[action]} {title}"
    pr_body = (
        f"Closes #{number}\n\n"
        f"类型：{ACTION_LABEL[action]}　提交人：{author or '未知'}\n\n{rows}\n\n"
        "机器人已检查：地址与头像可访问、字段格式、无重复。\n\n"
        "合并前请人工确认：\n"
        "- [ ] 对方站点确实添加了本站链接（新增时）\n"
        "- [ ] 站点内容符合收录标准\n"
        "- [ ] 修改/删除的提交人与该友链确有关系\n"
    )
    return pr_title, pr_body


def main():
    number = os.environ["ISSUE_NUMBER"]
    author = os.environ.get("ISSUE_AUTHOR", "")
    out = Path(os.environ.get("OUT_DIR", "."))
    network = os.environ.get("FRIEND_LINK_OFFLINE") != "1"

    form = parse_issue(os.environ["ISSUE_BODY"])
    lines = BLOGROLL.read_text(encoding="utf-8").split("\n")
    entries, _, _ = parse_entries(lines)
    action, errors = validate(form, entries, network)

    if errors:
        text = "友链检查未通过，请编辑本 Issue 修正后会自动重新检查：\n\n"
        text += "\n".join(f"- ❌ {e}" for e in errors)
        (out / "comment.md").write_text(text + "\n", encoding="utf-8")
        result = "false"
    else:
        fields = {k: form.get(k, "") for k in (*FIELDS, "new_website")}
        new_lines = apply_edit(lines, action, fields)
        if new_lines == lines:
            raise FormatError("edit produced no change")
        new_entries, _, _ = parse_entries(new_lines)
        expected = len(entries) + {"add": 1, "update": 0, "remove": -1}[action]
        if len(new_entries) != expected:
            raise FormatError("entry count changed unexpectedly")
        BLOGROLL.write_text("\n".join(new_lines), encoding="utf-8")
        title, body = pr_text(action, fields, number, author)
        (out / "pr_title.txt").write_text(title, encoding="utf-8")
        (out / "pr_body.md").write_text(body, encoding="utf-8")
        result = "true"

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"ok={result}\n")
    print(f"ok={result}")
    for e in errors:
        print(f"error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
