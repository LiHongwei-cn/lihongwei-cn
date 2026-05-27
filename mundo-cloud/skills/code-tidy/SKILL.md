---
name: code-tidy
description: >
  代码洁癖级整理 — 清除死代码、冗余注释、未用导入；统一排序与结构；
  每次写代码后自动触发。MUST trigger when user says: "整理代码", "tidy code",
  "clean code", "代码洁癖", "清理代码", "整理一下代码", "清理系统",
  "清理垃圾", "清理残留", or after any significant code edit session,
  package installation, or file download. Also trigger when the user
  expresses dissatisfaction with code organization or mentions OCD/cleanliness.
---

# 代码洁癖

> 代码如房间——所有东西在正确的位置，按顺序排列，不留冗余。

## 执行流程

### 第一步：扫描

逐文件扫描当前改动涉及的所有文件：

1. **无用 import**：`grep` 检查每个 import 是否在文件中被使用
2. **死函数**：检查定义了但从未调用的函数/方法
3. **注释掉的代码**：查找被 `//` `#` `/* */` 注释掉的代码块（不是说明性注释）
4. **冗余注释**：函数名已经说明意图的行内注释、`// TODO` 已完成的注释
5. **多余文件**：临时 `.md`、`.txt`、`test_*.tmp`、备份文件

### 第二步：排序

检查并修正元素顺序：

- **Imports**：标准库 → 第三方 → 本地模块，组内字母序
- **JSON keys**：字母序排列
- **CSS 属性**：定位 → 盒模型 → 排版 → 视觉 → 其他
- **HTML 属性**：`id` → `class` → `style` → `data-*` → `href/src` → 其他
- **函数定义**：public → private，同组内按依赖关系排列（被调用者在前）

### 第三步：清理

实际执行清理操作：

```
# 删除未使用的 import
# 删除死函数
# 删除注释掉的代码块
# 删除冗余注释
# 删除多余文件
# 排序 imports / keys / attributes
```

### 第四步：验证

清理完成后确认：
- [ ] 代码能正常运行（不因清理而破坏）
- [ ] 没有引入新的 lint 错误
- [ ] 文件行数有减无增（或者增的只是必要的逻辑）

## 特殊规则

### 不清理的情况
- 用户明确要求保留的代码
- 虽然未使用但是 API 导出的一部分（如 `__all__`、`exports`）
- 文档中引用的示例代码
- 打算后续使用的 TODO 注释（需有明确的后续计划和日期）

### CSS 属性排序参考
```
1. 定位: position, top, right, bottom, left, z-index
2. 盒模型: display, width, height, margin, padding, border
3. 排版: font-*, text-*, line-height, letter-spacing
4. 视觉: color, background, opacity, box-shadow
5. 其他: cursor, transition, transform, animation
```

### HTML 属性排序参考
```
1. id
2. class  
3. style
4. data-* (按字母序)
5. href / src / alt
6. type / name / value
7. target / rel / download
8. 事件属性 on*
```

## 安装残留清理

每次 `brew install`、`pip install`、`npm install`、文件下载后，执行：

### 自动清理步骤
```
# 包管理器缓存
brew cleanup                    # Homebrew 旧版本
pip3 cache purge                # pip 下载缓存
npm cache clean --force         # npm 缓存

# 安装包残留
find ~/Downloads -name "*.dmg" -delete
find ~/Downloads -name "*.pkg" -delete

# 临时目录
find /tmp -maxdepth 1 -user $(whoami) -delete 2>/dev/null

# .DS_Store（项目中）
find . -name ".DS_Store" -delete

# Python 编译缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
```

### 清理检查清单
- [ ] `.dmg` / `.pkg` 安装包已删除
- [ ] 解压的临时文件夹已删除
- [ ] `brew cleanup` 已执行
- [ ] `pip cache` 已清除
- [ ] 项目内无 `.DS_Store`
- [ ] 项目内无 `__pycache__` / `*.pyc`
