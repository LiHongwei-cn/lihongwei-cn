---
name: cross-platform-launcher
description: >
  创建跨平台项目启动器：HTML 可视化页面 + macOS .command 脚本 + Windows .bat 脚本。
  自动检测应用程序路径 + 菜单式交互。触发：启动器、launcher、一键启动、双击即用、
  桌面快捷方式、不想点 bat 文件。适用于 MATLAB、CCS、Hermes 等任何需要简化启动流程的工具。
---

# 跨平台启动器制作

为任何命令行工具创建傻瓜式启动器，让用户双击就能用，不再手动敲命令。

## 三步法

### 1. HTML 页面 — 两种格式

根据场景选择：

**格式 A：完整项目介绍页（推荐，用于项目主页）**

参照 `matlab-tool/index.html` 或 `matlab-ai/index.html`。结构：
- Hero 区（渐变标题 + 一句话描述 + badge）
- 下载区（大按钮 + 备选链接 + 文件信息）
- 工作流程区（4 卡片 feature-grid）
- 步骤教程区（step-list 带自动编号）
- 详情卡片网格（sim-grid，每卡片含图标/参数/描述/输出/命令）
- 兼容性区（feature-grid）
- 文件列表区（file-group + file-list）
- Footer（GitHub + 协议 + busuanzi 计数器）

CSS 标准：
- `:root{--bg1:#0f0c29;--bg2:#302b63;--bg3:#24243e;--accent:#6c8cff;...}`
- 渐变背景 `background:linear-gradient(135deg,var(--bg1),var(--bg2),var(--bg3))`
- 卡片 `background:var(--card);border:1px solid var(--border);border-radius:14px`
- 步骤编号用 CSS counter `counter-increment:step`
- 响应式 `max-width:900px`

必含元素：
- busuanzi 计数器：`<div class="page-counter">本页被阅读 <span id="busuanzi_page_pv">...</span> 次</div>`
- busuanzi 脚本：`<script defer src="https://jsd.dusays.com/npm/penndu@17.0.0/bsz.js"></script>`
- 返回链接：`<a class="back-link" href="../">← 返回主页</a>`
- 底部 GitHub + MIT 声明

详见 `references/project-page-template.md`

**格式 B：交互式启动器（用于工具选择/命令生成）**

轻量交互页，含：
- AI 助手指令生成区 + 复制按钮
- 功能卡片网格（点击切换命令）
- 底部下载启动脚本链接

设计规范同格式 A 的 CSS 变量体系，但内容更轻量。适合 ccs-launcher、desktop-launcher 等工具型页面。

### 2. macOS .command 启动脚本

```bash
#!/bin/bash
# 脚本头：检测应用程序路径
for candidate in \
  "/Applications/AppName.app/Contents/MacOS/app" \
  "/usr/local/bin/app"; do
  if [ -f "$candidate" ]; then APP="$candidate"; break; fi
done

# 未检测到时给出备选方案
if [ -z "$APP" ]; then
  echo "[X] 未检测到应用"
  echo "  1) 打开启动器网页"
  echo "  2) 手动操作说明"
  read -p "选项: " choice
  # ...
fi

# 菜单式交互
echo "  1) 功能A"
echo "  2) 功能B"
read -p "选项: " choice
```

**关键点**：
- 用 `for` 循环检测多版本安装路径
- 未找到时提供网页版备选
- `read -p` 菜单降低上手门槛
- 创建后 `chmod +x` 赋予执行权限

### 3. Windows .bat 启动脚本

```bat
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 检测应用路径
set "APP="
for %%v in (2024b 2023b 2022b) do (
    if exist "C:\Path\%%v\bin\app.exe" set "APP=..."
)

:: 无应用时的备选
if "%APP%"=="" goto :no_app

:menu
echo 请选择：
echo   1) 功能A
echo   2) 功能B
set /p "CHOICE=选项: "
```

**关键点**：
- `chcp 65001` 避免中文乱码
- `setlocal enabledelayedexpansion` 支持变量动态更新
- `goto` 标签实现菜单循环
- 路径中的反斜杠需要双写 `\\`（如传给 MATLAB 的 `-r` 参数）

## macOS .app 启动器（放入程序坞）

当用户要求"放进 Dock""程序坞""桌面图标""双击启动应用"时，创建完整的 .app bundle：

1. 创建目录：`mkdir -p ~/Applications/AppName.app/Contents/{MacOS,Resources}`
2. 写入 `Info.plist`（CFBundleExecutable 必须与 MacOS/ 下脚本名一致）
3. 写入启动脚本（用 osascript 打开 Terminal.app 执行命令）
4. 生成自定义图标：Python PIL 画 1024x1024 PNG → `iconutil -c icns` 转换
5. 添加到 Dock：`defaults write com.apple.dock persistent-apps -array-add '...'` + `killall Dock`

完整流程、Info.plist 模板、图标生成代码、Dock 命令见 `references/macos-app-bundle.md`。

**关键坑**：
- `CFBundleExecutable` 和 `CFBundleIconFile` 必须与实际文件名完全匹配
- iconset 必须包含 @2x 变体（Retina 屏幕），否则图标模糊
- `killall Dock` 安全，会自动重启，不丢失其他图标
- .app 放在 `~/Applications/`（用户目录），不是 `/Applications/`（系统目录）

## Logo / 图标集成

启动器页面应展示工具的官方 logo（而非纯 emoji）：

1. 从官方仓库获取 logo（通常在 `website/static/img/logo.png` 或 `web/public/`）
2. 复制到子项目目录（如 `hermes-launcher/hermes-logo.png`）
3. HTML 页面 hero 区添加 `<img src="hermes-logo.png" class="hero-logo">`
4. CSS 添加 `.hero-logo{width:120px;height:120px;margin-bottom:20px;border-radius:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3)}`
5. 主页卡片 icon 用 `<img>` 替代 emoji：`<img src="子目录/logo.png" style="width:28px;height:28px;border-radius:6px">`
6. 如需 macOS .app 启动器 + 自定义图标，见 `references/macos-app-bundle.md`

## 同步规则

启动器创建后必须：
1. 在主页 `index.html` 添加入口卡片
2. 上传 `.command` 到 `tools/` 目录并 chmod +x
3. 上传 `.bat` 到 `tools/` 目录
4. 创建子项目 `README.md`（格式见 `references/project-readme-template.md`）
5. 在主 `README.md` 中添加该项目的 `##` 章节入口
6. 创建 GitHub Release 托管安装包（见「安装包发布」）
7. Git add + commit + push

**关键约束**：主 README.md 的 `##` 章节、目录树、主页 index.html 卡片必须三者同步增删。新增项目时三处都加，移除项目时三处都删。主页卡片 icon 使用工具 logo 图片（而非 emoji）。

## 安装包发布

用 GitHub Releases 统一托管所有安装包（不直接用 raw.githubusercontent.com）：

```bash
# 打包 macOS .app（如有）
cd tools && zip -r ../YourApp.app.zip "YourApp.app"

# 创建 Release 并上传所有文件
gh release create packages \
  --title "安装包合集" \
  --notes "所有安装包。" \
  matlab-tool/xxx.zip \
  tools/xxx.bat \
  tools/xxx.command \
  YourApp.app.zip
```

Release 下载链接格式：
```
https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/filename
```

README 中所有下载链接统一指向 Release URL，主 README 头部加「所有安装包」入口链接指向 Release 页面。

## 项目移除流程

当用户要去掉某项目展示时，清理三处入口（保留子目录代码）：
1. 主页 `index.html` → 删除 `<a class="card" ...>` 整块
2. 主 `README.md` → 删除 `##` 章节 + 目录树中对应行
3. 子目录不动（代码留存）

## 仓库健康检查

用户说"检查仓库"或"有没有损坏"时，按 `references/repo-health-check.md` 逐项检查。
常见问题：缺失 LICENSE、shell 脚本无执行权限、主页链接断裂、敏感文件泄露。

注意：`404.html` 是 GitHub Pages 自定义 404 页面，有用，不要删除。

## 系统垃圾清理

用户说"清理垃圾""清除残留""清理缓存"时，按 `references/garbage-cleanup.md` 执行系统化清理。

## 教程页面去重

多个页面覆盖重叠内容时（如"一键启动器"和"完整指南"），按 `references/tutorial-deduplication.md` 处理：
- 起始页添加分流提示（"还没安装？去看完整指南"）
- 详细教程添加快速入口（"已安装？直接去启动器"）
- 重叠章节改为验证（`hermes --version`），不重复安装步骤
- 双向交叉引用

## 与 homepage-layout 的边界

- `homepage-layout`：负责主页布局自检和链接验证
- `cross-platform-launcher`：负责创建新的启动器页面和脚本
- 两者分工：launcher 创建 → homepage-layout 校验
