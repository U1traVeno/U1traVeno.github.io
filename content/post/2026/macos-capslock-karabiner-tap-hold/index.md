---
title: "使用 Karabiner-Elements 在 macOS 修改 Capslock 长按短按触发信号"
description: 
date: 2026-09-25T04:00:00+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: false
tags: ['Workflow']
---

macOS 用 Caps Lock 切中英（`ABC` ↔ 双拼）有一两百毫秒延迟，快按还经常没反应，打字经常卡手

## 根因

1. **HID 层故意延迟**。Apple 开源的 `IOHIDKeyboardFilter.mm`（IOHIDFamily）里 `#define kCapsLockDelayMS 75`，`processCapsLockDelay` 对"激活方向"的按下先扣住、开定时器（注释原文 "kill the down event"），快按则 down/up 整对丢弃。官方说法（HT201509，存档）：

   > "The Caps Lock function on these computers is designed to reduce accidental activation. You must press and hold down the key slightly longer to activate the caps lock function."

   实际生效门槛约 100ms（pqrs 的测量），这就是"按了没反应"的主因。

2. **输入源切换是异步流水线**。HIToolbox/TSM → `TISSelectInputSource` → 通知 → 各 App 的 input context；切进 `com.apple.inputmethod.SCIM` 这类 IMK 输入法还要等 `imklaunchagent` 建 `IMKInputSession`，空闲后首次切换更慢。

## 配置脚本

附上一个可以直接指导完成安装配置的脚本[`wizard-karabiner-capslock.sh`](https://github.com/U1traVeno/U1traVeno.github.io/blob/main/content/post/2026/macos-capslock-karabiner-tap-hold/wizard-karabiner-capslock.sh) 分阶段确认、每个操作先看清再执行、自动落时间戳过程日志。下面的步骤已经全部包含在脚本里。我使用 macOS Tahoe 26.6.2，其他版本未经测试。

## 修复

短按切输入法，长按是大写锁。使用 Karabiner-Elements，官方文档明确说解决了延迟问题：

> "Karabiner-Elements disables the caps lock delay without any action since v13.3.0."

### 1. 安装与授权

```bash
brew install --cask karabiner-elements
```

装完批准 DriverKit 系统扩展并授权。macOS Tahoe 的入口是「系统设置 → 登陆项与扩展 → 拓展 → 按类别 → 驱动程序扩展」（旧版在「通用 → 登录项与扩展」），再打开 Karabiner 的后台服务和辅助功能。用这个确认扩展真的批了——没批时状态是 `[activated waiting for user]`，此时一切规则都无效：

```bash
systemextensionsctl list | grep pqrs   # 期望 [activated enabled]
```

### 2. 规则：短按 → F18，长按 → Caps Lock

`~/.config/karabiner/assets/complex_modifications/capslock-tap-f18-hold-capslock.json`：

```json
{
  "title": "Caps Lock: tap → F18 (switch input source), hold → Caps Lock",
  "rules": [
    {
      "description": "Caps Lock: tap → F18 (select next input source), hold (≥250ms) → Caps Lock toggle",
      "manipulators": [
        {
          "type": "basic",
          "from": { "key_code": "caps_lock", "modifiers": { "optional": ["any"] } },
          "to_if_alone": [{ "key_code": "f18" }],
          "to_if_held_down": [{ "key_code": "caps_lock", "hold_down_milliseconds": 200 }],
          "parameters": {
            "basic.to_if_alone_timeout_milliseconds": 250,
            "basic.to_if_held_down_threshold_milliseconds": 250
          }
        }
      ]
    }
  ]
}
```

语义与 keyd 的 `timeout(f14, 250, capslock)` 逐项对齐：松手快于 250ms 发 `f18`，按住满 250ms 发一次真 `caps_lock`。`hold_down_milliseconds: 200` 是让合成的 down/up 保持足够长，不被 HID 层的防误触吞掉（官方 rule 同款做法）。写好后在 Karabiner-Elements → Complex Modifications → Add rule 里 Enable。

### 3. 系统设置

- 「键盘 → 键盘快捷键… → 输入」：把**选择"输入"菜单中的下一个输入法**绑到 **F18**。MacBook 没有 F18 实体键——规则生效后**快按一下 Caps Lock 就是 F18**，直接录进去。
- 关掉**使用 Caps Lock 键切换到和从 ABC**。不关的话，长按发出来的 `caps_lock` 会被它吞去切输入法，大写锁就废了。

> 不要用 Karabiner 的 `select_input_source` 切中文输入法：官方文档明确它对 CJKV（有 `input_mode_id` 的）输入法会失败，走系统快捷键最稳。

## 验证

短按立刻切输入法、长按切大写锁、再长按切回。用 Karabiner-EventViewer 或下面的探针看实际发出的事件：短按应看到 `keyDown f18 (79)`，长按看到 `flagsChanged caps_lock (57)` 且大写状态正常翻转。

**未做毫秒级测量**。改前改后的对比只有主观感受：快按不再被丢，切换即时发生；输入法冷启动那点延迟仍在（那是根因第 2 段，跟按键无关）。

## 回滚

KE 里 Disable 该规则；系统设置解绑 F18、勾回"使用 Caps Lock 键切换到和从 ABC"；彻底卸载用 `brew uninstall --cask karabiner-elements`。副作用只有一个：Caps Lock 不再是即按即大写锁。

## 附

- [`keyprobe.swift`](https://github.com/U1traVeno/U1traVeno.github.io/blob/main/content/post/2026/macos-capslock-karabiner-tap-hold/keyprobe.swift) —— 按键事件探针（listen-only CGEventTap），`swift keyprobe.swift` 直接跑，首次运行要给终端「输入监控」授权。

## 参考

- [Apple OSS · IOHIDFamily/IOHIDKeyboardFilter.mm](https://github.com/apple-oss-distributions/IOHIDFamily)：`kCapsLockDelayMS 75`、`processCapsLockDelay` 的 "kill the down event" / "kill the up event"
- [Apple HT201509（存档）](https://web.archive.org/web/20150115033359/https://support.apple.com/en-us/HT201509)："designed to reduce accidental activation"
- [Karabiner-Elements · disable caps lock delay](https://karabiner-elements.pqrs.org/docs/help/how-to/disable-caps-lock-delay/)
- [Karabiner-Elements · to.select_input_source](https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/to/select-input-source/)（CJKV 警告）
- [Karabiner-Elements · required macOS settings](https://karabiner-elements.pqrs.org/docs/manual/misc/required-macos-settings/)
- [Apple TN2450](https://developer.apple.com/library/archive/technotes/tn2450/_index.html)（`hidutil` 重映射备选方案及其代价）
