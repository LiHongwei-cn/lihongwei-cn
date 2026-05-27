# 项目 README 模板

每个子项目目录下应有一个 `README.md`，结构统一，方便 GitHub 浏览和 Profile 主页展示。

## 模板结构

```markdown
# 项目名称

一句话简介。核心卖点 + 适用场景。

## 下载（如适用）

| 平台 | 下载 |
|------|------|
| Windows | [文件名.bat](raw下载链接) |
| macOS | [文件名.command](raw下载链接) |

右键另存为，放到工作目录，双击即可。

### macOS Dock 固定（可选）

如项目需要，附上 .app 创建脚本。

## 工作原理

用箭头流展示：`步骤A → 步骤B → 步骤C`

## 前置条件

### 1. 安装 X
```bash
安装命令
```

### 2. 配置 Y
```bash
配置命令
```

## 使用方式

分步骤说明（可选含桌面快捷方式创建）。

## 自定义配置（可选）

高级用法，修改哪些变量可以实现什么效果。

## 常见问题

- **问题A**：解答A
- **问题B**：解答B

## 详情

[项目页面](https://lihongwei-cn.github.io/lihongwei-cn/项目目录/) · [相关链接]
```

## 关键规则

1. 每个子项目必须有自己的 `README.md`
2. 下载链接用 raw.githubusercontent.com 直链
3. Win/Mac 双平台都必须覆盖
4. 末尾链向项目 HTML 页面（GitHub Pages）
5. 主 README.md 中必须有该项目的入口章节

## 主 README 入口格式

每个子项目在主 README.md 中占用一个 `##` 章节：

```markdown
## 项目名称

简介（1-2 句）。

- **Windows**：[下载 xxx.bat](raw链接)
- **macOS**：[下载 xxx.command](raw链接)

链接符号：[项目页面](HTML页面) ｜ [README](子目录/README.md)
```
