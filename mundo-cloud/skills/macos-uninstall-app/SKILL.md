---
name: macos-uninstall-app
description: >
  干净卸载 macOS 应用程序（包括带 root 守护进程的顽固软件）。
  触发词：卸载、uninstall、删除应用、remove app、清理残留、clean up app、
  卸载干净、remove completely、XX 卸不掉。
  适用于任何需要深度清理的 macOS 应用，尤其是带 LaunchDaemon/Agent 的远程控制、
  VPN、杀毒、系统工具类软件。
---

# macOS 应用深度卸载

## 核心流程

### 第一步：侦察（必须先做）

用 `search_files` + `terminal` 找出应用的所有痕迹：

```bash
# 1. 找主程序
search_files(path="/Applications", pattern="*AppName*", target="files")

# 2. 找进程
pgrep -fl -i appname

# 3. 找所有残留文件（7 个位置）
find /Library/LaunchAgents /Library/LaunchDaemons \
     ~/Library/LaunchAgents ~/Library/Preferences \
     ~/Library/Application\ Support ~/Library/Caches \
     ~/Library/Logs ~/Library/Containers ~/Library/HTTPStorages \
     ~/Library/Saved\ Application\ State \
     -maxdepth 2 -iname "*appname*" -o -iname "*com.vendor.*" 2>/dev/null

# 4. 安装包记录
find /var/db/receipts -iname "*appname*" 2>/dev/null

# 5. 共享文件
ls /Users/Shared/*AppName* 2>/dev/null

# 6. 全盘搜索
mdfind "kMDItemDisplayName == 'AppName'" 2>/dev/null
```

**检查反向 DNS 标识**：从 app 的 Info.plist 拿 Bundle ID（如 `com.netease.uuremote`），
用 Bundle ID 再搜一遍，能找到很多漏网之鱼。

### 第二步：停止服务

```bash
# 先卸载 LaunchAgent/Daemon（停止自启动）
sudo launchctl unload /Library/LaunchDaemons/com.vendor.daemon.plist
sudo launchctl unload /Library/LaunchAgents/com.vendor.agent.plist
sudo launchctl remove com.vendor.daemon
sudo launchctl remove com.vendor.agent

# 再杀进程
sudo killall -9 AppNameDaemon
sudo killall -9 AppNameService
sudo killall -9 AppName
```

**顺序很重要**：先 unload 再 kill，否则守护进程可能自动重启。

### 第三步：删除文件

按以下顺序清理，每类都是 `sudo rm -rf`：

1. `/Applications/AppName.app`
2. `/Library/LaunchAgents/com.vendor.*.plist`
3. `/Library/LaunchDaemons/com.vendor.*.plist`
4. `~/Library/Preferences/com.vendor.*`
5. `~/Library/Application Support/com.vendor.*`
6. `~/Library/Caches/com.vendor.*`（含 SentryCrash 子目录）
7. `~/Library/HTTPStorages/com.vendor.*`
8. `~/Library/Logs/com.vendor.*`
9. `~/Library/Containers/com.vendor.*`
10. `~/Library/Saved Application State/com.vendor.*`
11. `/var/db/receipts/com.vendor.*`（安装包记录）
12. `/Users/Shared/AppName`（共享数据）

### 第四步：验证

```bash
pgrep -fl -i appname          # 应无输出
mdfind "kMDItemDisplayName == 'AppName'"  # 应无输出
```

## 关键 Pitfall

### Pitfall 1：sudo 密码不能通过终端工具传入

Hermes 的 terminal 工具**安全策略禁止** `echo password | sudo -S` 模式。
遇到需要 sudo 的操作，必须生成一条用户可粘贴的完整命令，让用户在自己的终端里执行。

**输出格式**：不要解释原因，直接给一段可粘贴的命令块。用户要的是"复制→粘贴→输入密码→done"。

```bash
# 给用户的命令示例（单行用 ; 连接，减少粘贴次数）
sudo killall -9 AppDaemon; sudo killall -9 AppService; sudo rm -rf /Applications/App.app; sudo rm -f /Library/LaunchDaemons/com.vendor.*.plist; echo "done"
```

看到 `done` 就说明执行完了。

### Pitfall 2：root 守护进程无法非 sudo 杀死

`kill -9 PID` 对 root 进程返回 `Operation not permitted`。
必须用 `sudo killall -9` 或 `sudo kill -9 PID`。

### Pitfall 3：LaunchDaemon vs LaunchAgent

- `/Library/LaunchDaemons/` → root 级，系统启动时运行，**必须 sudo 卸载**
- `/Library/LaunchAgents/` → 用户登录时运行，但 `/Library/` 下的仍需 sudo
- `~/Library/LaunchAgents/` → 用户级，不需要 sudo

### Pitfall 4：receipt 文件

`/var/db/receipts/` 下的 `.plist` 和 `.bom` 是 macOS 安装包记录，
不删不影响运行，但会导致系统认为应用仍"已安装"。清理要彻底就一起删。

## 快速参考：常见顽固应用的 Bundle ID 前缀

| 应用 | Bundle ID 前缀 |
|------|----------------|
| UU 远程 | `com.netease.uuremote` |
| ToDesk | `com.todesk.*` |
| 向日葵 | `com.oray.sunlogin*` |
| TeamViewer | `com.teamviewer.*` |
| ClashX | `com.west2online.clashx*` |
| 腾讯柠檬 | `com.tencent.lemon*` |
| 网易有道 | `com.youdao.*` |
