// keyprobe.swift — 打印系统/应用实际收到的按键事件（KE 重映射之后的最终输出）。
//
// 用法：  swift "$TMPDIR/keyprobe.swift"
//   或编译： swiftc -O keyprobe.swift -o keyprobe && ./keyprobe
// 退出：  Ctrl-C
//
// 首次运行 macOS 会弹「输入监控」授权（给终端 App）：
//   系统设置 → 隐私与安全性 → 输入监控 → 打开终端对应项，然后重新运行。
//
// 验证目标（配合 caps_lock tap→f18 / hold→caps_lock 规则）：
//   快按 Caps Lock(<250ms) → keyDown f18 (79) + keyUp f18 (79)
//   长按 Caps Lock(≥250ms) → flagsChanged caps_lock (57) [CAPS=ON]（再长按 → CAPS=off）
// 若看到的是 caps_lock (57) 的 keyDown/keyUp 而没有 f18 → KE 规则未生效。
//
// 注意：本脚本只做 listen-only，不注入、不修改任何事件。

import CoreGraphics
import Foundation

let keyNames: [Int: String] = [
    0: "a", 1: "s", 2: "d", 3: "f", 4: "h", 5: "g", 6: "z", 7: "x", 8: "c", 9: "v",
    11: "b", 12: "q", 13: "w", 14: "e", 15: "r", 16: "y", 17: "t", 18: "1", 19: "2",
    20: "3", 21: "4", 22: "6", 23: "5", 24: "=", 25: "9", 26: "7", 27: "-", 28: "8",
    29: "0", 30: "]", 31: "o", 32: "u", 33: "[", 34: "i", 35: "p", 36: "return",
    37: "l", 38: "j", 39: "'", 40: "k", 41: ";", 42: "\\", 43: ",", 44: "/", 45: "n",
    46: "m", 47: ".", 48: "tab", 49: "space", 50: "`", 51: "delete", 53: "esc",
    54: "right_command", 55: "command", 56: "shift", 57: "caps_lock", 58: "option",
    59: "control", 60: "right_shift", 61: "right_option", 62: "right_control", 63: "fn",
    64: "f17", 65: "keypad_.", 67: "keypad_*", 69: "keypad_+", 71: "clear",
    75: "keypad_/", 76: "keypad_enter", 78: "keypad_-", 79: "f18", 80: "f19",
    81: "keypad_=", 82: "keypad_0", 83: "keypad_1", 84: "keypad_2", 85: "keypad_3",
    86: "keypad_4", 87: "keypad_5", 88: "keypad_6", 89: "keypad_7", 90: "f20",
    91: "keypad_8", 92: "keypad_9",
    96: "f5", 97: "f6", 98: "f7", 99: "f3", 100: "f8", 101: "f9", 103: "f11",
    105: "f13", 106: "f16", 107: "f14", 109: "f10", 111: "f12", 113: "f15",
    114: "help", 115: "home", 116: "page_up", 117: "forward_delete", 118: "f4",
    119: "end", 120: "f2", 121: "page_down", 122: "f1", 123: "left", 124: "right",
    125: "down", 126: "up",
]

func keyName(_ code: Int64) -> String {
    keyNames[Int(code)] ?? "keycode_\(code)"
}

var lastTs: UInt64 = 0
var gTap: CFMachPort? // 仅用于 tap 被禁用后重新启用

func tapCallback(
    proxy: CGEventTapProxy, type: CGEventType, event: CGEvent,
    refcon: UnsafeMutableRawPointer?
) -> Unmanaged<CGEvent>? {
    // tap 被系统禁用（超时/用户输入）时重新启用
    if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
        if let t = gTap { CGEvent.tapEnable(tap: t, enable: true) }
        return Unmanaged.passUnretained(event)
    }

    let code = event.getIntegerValueField(.keyboardEventKeycode)
    let ts = event.timestamp // 纳秒（开机时钟）
    let deltaMs = lastTs == 0 ? 0.0 : Double(ts &- lastTs) / 1_000_000.0
    lastTs = ts

    let label: String
    switch type {
    case .keyDown: label = "keyDown  "
    case .keyUp: label = "keyUp    "
    case .flagsChanged: label = "flagsChg "
    default: label = "type(\(type.rawValue))"
    }

    var extra = ""
    if type == .flagsChanged {
        let caps = event.flags.contains(.maskAlphaShift) ? "CAPS=ON" : "CAPS=off"
        extra = "  [\(caps)]"
    }

    let tMs = String(format: "%12.1f", Double(ts) / 1_000_000.0)
    let dMs = String(format: "%8.1f", deltaMs)
    print("\(tMs) ms  (+\(dMs) ms)  \(label)  \(keyName(code)) (\(code))\(extra)")
    fflush(stdout)
    return Unmanaged.passUnretained(event)
}

let mask: CGEventMask =
    (CGEventMask(1) << CGEventType.keyDown.rawValue)
    | (CGEventMask(1) << CGEventType.keyUp.rawValue)
    | (CGEventMask(1) << CGEventType.flagsChanged.rawValue)

guard let tap = CGEvent.tapCreate(
    tap: .cgSessionEventTap,
    place: .headInsertEventTap,
    options: .listenOnly,
    eventsOfInterest: mask,
    callback: tapCallback,
    userInfo: nil
) else {
    print("""
    ✗ 创建事件监听失败：没有「输入监控」或「辅助功能」权限。
      系统设置 → 隐私与安全性 → 输入监控 → 允许你运行本脚本的终端 App，
      然后重新运行。（若没有弹过授权，先手动加：/usr/bin/swift 或终端 App）
    """)
    exit(1)
}

gTap = tap

print("keyprobe: 监听中（显示的是应用实际收到的最终事件）… 按键试试，Ctrl-C 退出")
print("  期望：快按 Caps Lock → f18 (79) down/up；长按 → flagsChanged caps_lock (57)")
print("")

let rl = CFRunLoopGetCurrent()
let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
CFRunLoopAddSource(rl, source, .commonModes)
CGEvent.tapEnable(tap: tap, enable: true)
CFRunLoopRun()
