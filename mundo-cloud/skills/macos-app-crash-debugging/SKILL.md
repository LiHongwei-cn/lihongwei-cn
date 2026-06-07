---
name: macos-app-crash-debugging
description: "诊断 macOS 原生应用崩溃（闪退）。触发词：闪退、崩溃、crash、闪退了、打不开、自动关闭、EXC_BAD_ACCESS、SIGSEGV、SIGBUS。适用于 Terminal、Finder、Safari、系统偏好设置等任何 macOS 原生应用。"
version: "1.0"
---

# macOS 应用崩溃调试

## 适用场景

- macOS 原生应用突然闪退/消失
- 用户报告"打不开"或"自动关闭"
- 应用启动后几秒内崩溃

## 核心流程

### 第 1 步：读崩溃日志

```bash
# 查找目标应用的崩溃报告
find ~/Library/Logs/DiagnosticReports -name "*<AppName>*" -type f | sort -r | head -5
# 也检查 Retired 目录
find ~/Library/Logs/DiagnosticReports/Retired -name "*<AppName>*" -type f | sort -r | head -5
```

### 第 2 步：解析崩溃签名

崩溃日志是 JSON 格式，重点关注：

- `exception.type`：崩溃类型
  - `EXC_BAD_ACCESS` → 内存访问越界/野指针
  - `EXC_CRASH` → 应用自己触发的异常
  - `EXC_RESOURCE` → 资源超限（CPU/内存）
- `exception.subtype`：具体地址和原因
  - `KERN_PROTECTION_FAILURE` → 访问受保护内存
  - `KERN_INVALID_ADDRESS` → 访问无效地址
- `termination.code`：
  - `11` (SIGSEGV) → 段错误
  - `10` (SIGBUS) → 总线错误
- `faultingThread` → 崩溃线程 ID
- `threads[].frames[0].symbol` → 崩溃函数名（最关键）

### 第 3 步：识别常见崩溃模式

| 崩溃函数 | 原因 | 修复 |
|---------|------|------|
| `_platform_memmove` in `restoreWindowWithIdentifier` | 窗口状态恢复损坏 | 禁用窗口恢复 + 清除 savedState |
| `objc_release` / `objc_msgSend` | 野指针/use-after-free | 重置应用偏好设置 |
| `CFStringCreateCopy` / `__CFStringAppend` | 字符串缓冲区溢出 | 清除缓存文件 |
| `IOKit` 相关 | 硬件/驱动问题 | 重置 SMC/NVRAM |
| `CoreGraphics` / `CGContext` | 渲染崩溃 | 更新 macOS / 清除字体缓存 |

### 第 4 步：修复

**模式 A：窗口恢复崩溃**（最常见的系统应用崩溃）

```bash
# 禁用窗口恢复
defaults write <bundle-id> NSQuitAlwaysKeepsWindows -bool false
# 清除窗口位置缓存
defaults delete <bundle-id> "NSWindow Frame <WindowName>" 2>/dev/null
# 清除 savedState
rm -rf ~/Library/Saved\ Application\ State/<bundle-id>.savedState 2>/dev/null
rm -rf ~/Library/Containers/<bundle-id>/Data/Library/Saved\ Application\ State/*.savedState 2>/dev/null
```

**模式 B：偏好设置损坏**

```bash
# 备份后重置
cp ~/Library/Preferences/<bundle-id>.plist ~/Library/Preferences/<bundle-id>.plist.bak
defaults delete <bundle-id>
```

**模式 C：缓存损坏**

```bash
# 清除应用缓存
rm -rf ~/Library/Caches/<bundle-id>/
# 清除容器缓存（沙盒应用）
rm -rf ~/Library/Containers/<bundle-id>/Data/Library/Caches/
```

**模式 D：持续崩溃无法修复**

```bash
# 重置应用所有数据（最后手段）
rm -rf ~/Library/Preferences/<bundle-id>.plist
rm -rf ~/Library/Containers/<bundle-id>/
rm -rf ~/Library/Saved\ Application\ State/<bundle-id>.savedState
rm -rf ~/Library/Caches/<bundle-id>/
```

## 常见应用的 bundle-id

| 应用 | bundle-id |
|------|-----------|
| Terminal | com.apple.Terminal |
| Finder | com.apple.finder |
| Safari | com.apple.Safari |
| 系统偏好设置 | com.apple.systempreferences |
| 活动监视器 | com.apple.ActivityMonitor |

## Pitfalls

1. **不要忽略 `find` 的 Retired 目录**：macOS 会把旧崩溃日志移到 `DiagnosticReports/Retired/`
2. **崩溃日志的 `procLaunch` 和 `captureTime` 差距很小** → 启动即崩溃，不是使用中崩溃
3. **连续多次崩溃**（如 3 次间隔 < 10 秒）→ macOS 自动重启应用导致连环崩溃
4. **`defaults delete` 后应用会重置为默认设置** → 提醒用户会丢失自定义配置
5. **沙盒应用（有 Containers 目录）和非沙盒应用的文件位置不同** → 两个路径都要检查
