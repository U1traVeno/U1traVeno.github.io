import unittest

import friend_link as fl

PAGE = """---
title: Blogroll
links:
  - title: Alpha
    description: first
    website: https://alpha.example/
    image: https://alpha.example/a.png

  - title: "Beta Site"
    website: "https://beta.example/"
    image: "https://beta.example/b.png"
    
  - title: Gamma
    description: third   
    website: https://gamma.example/
    image: https://gamma.example/g.png

menu:
  main:
    weight: -50

comments: false
---

body
"""

CONFIRM = "- [x] 我已在我的站点添加了本站的友链 / I have linked back to this site\\n- [x] 我的站点符合 README 里的收录标准"


def issue(action, **kw):
    f = {"action": action, "title": "", "website": "", "image": "", "description": "", "new_website": "",
         "confirm": CONFIRM.replace("\\n", "\n")}
    f.update(kw)
    return f


def lines():
    return PAGE.split("\n")


def entries():
    return fl.parse_entries(lines())[0]


class ParseIssue(unittest.TestCase):
    def test_sections_and_no_response(self):
        body = (
            "### 类型 / Type\r\n\r\n新增 / Add\r\n\r\n### 站点名称 / Site name\r\n\r\nDelta\r\n\r\n"
            "### 一句话简介 / Description（可选，最多 40 字）\r\n\r\n_No response_\r\n"
        )
        got = fl.parse_issue(body)
        self.assertEqual(got["action"], "新增 / Add")
        self.assertEqual(got["title"], "Delta")
        self.assertEqual(got["description"], "")


class Edit(unittest.TestCase):
    def test_add_appends_after_last_entry(self):
        out = fl.apply_edit(lines(), "add", {"title": "Delta", "website": "https://d.example/",
                                             "image": "https://d.example/d.png", "description": ""})
        new = fl.parse_entries(out)[0]
        self.assertEqual([e["title"] for e in new], ["Alpha", "Beta Site", "Gamma", "Delta"])
        text = "\n".join(out)
        self.assertIn('    image: "https://d.example/d.png"\n\nmenu:', text)
        # untouched entries are byte-identical
        self.assertTrue(text.startswith(PAGE[: PAGE.index("  - title: Gamma")]))

    def test_quotes_are_escaped(self):
        out = fl.apply_edit(lines(), "add", {"title": 'He said "hi"\\', "website": "https://q.example/",
                                             "image": "https://q.example/q.png", "description": ""})
        self.assertEqual(fl.parse_entries(out)[0][-1]["title"], 'He said "hi"\\')

    def test_update_changes_only_target(self):
        out = fl.apply_edit(lines(), "update", {"title": "", "description": "new desc", "image": "",
                                                "website": "https://beta.example", "new_website": ""})
        new = fl.parse_entries(out)[0]
        self.assertEqual(new[1]["description"], "new desc")
        self.assertEqual(new[1]["title"], "Beta Site")
        self.assertEqual(new[0], {**entries()[0]})
        self.assertEqual(len(new), 3)

    def test_update_new_website(self):
        out = fl.apply_edit(lines(), "update", {"title": "", "description": "", "image": "",
                                                "website": "https://alpha.example/", "new_website": "https://alpha2.example/"})
        self.assertEqual(fl.parse_entries(out)[0][0]["website"], "https://alpha2.example/")

    def test_remove_middle_and_last(self):
        mid = fl.apply_edit(lines(), "remove", {"website": "https://beta.example/"})
        self.assertEqual([e["title"] for e in fl.parse_entries(mid)[0]], ["Alpha", "Gamma"])
        last = fl.apply_edit(lines(), "remove", {"website": "https://gamma.example/"})
        text = "\n".join(last)
        self.assertEqual([e["title"] for e in fl.parse_entries(last)[0]], ["Alpha", "Beta Site"])
        self.assertIn("\n\nmenu:", text)
        self.assertNotIn("Gamma", text)

    def test_remove_first(self):
        out = fl.apply_edit(lines(), "remove", {"website": "https://alpha.example/"})
        self.assertEqual([e["title"] for e in fl.parse_entries(out)[0]], ["Beta Site", "Gamma"])


class Validate(unittest.TestCase):
    def run_validate(self, form):
        return fl.validate(form, entries(), network=False)

    def test_add_ok(self):
        action, errors = self.run_validate(issue("新增 / Add", title="D", website="https://d.example/", image="https://d.example/d.png"))
        self.assertEqual((action, errors), ("add", []))

    def test_add_rejects(self):
        _, errors = self.run_validate(issue("新增 / Add", title="D", website="http://d.example/", image=""))
        self.assertEqual(len(errors), 1)  # https error stops early
        _, errors = self.run_validate(issue("新增 / Add", title="D", website="https://www.alpha.example", image="https://x.example/i.png"))
        self.assertTrue(any("已经在友链" in e for e in errors))
        _, errors = self.run_validate(issue("新增 / Add", title="D", website="https://d.example/", image="",
                                            description="x" * 41, confirm="- [ ] linked back\n- [x] README"))
        self.assertEqual(len(errors), 3)

    def test_update_and_remove_need_existing(self):
        _, errors = self.run_validate(issue("修改 / Update", website="https://nope.example/", description="x"))
        self.assertTrue(any("找不到" in e for e in errors))
        action, errors = self.run_validate(issue("删除 / Remove", website="https://alpha.example/", confirm=""))
        self.assertEqual((action, errors), ("remove", []))

    def test_update_needs_a_change(self):
        _, errors = self.run_validate(issue("修改 / Update", website="https://alpha.example/"))
        self.assertTrue(any("没有填写" in e for e in errors))

    def test_private_hosts_rejected(self):
        self.assertIsNotNone(fl.probe("https://127.0.0.1/x.png", True))


if __name__ == "__main__":
    unittest.main()
