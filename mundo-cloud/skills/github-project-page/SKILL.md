---
name: github-project-page
description: 创建或更新 GitHub Pages 项目页面。当用户要求新增项目、创建项目页面、更新主页、添加项目卡片时自动触发。覆盖完整工作流：目录结构、README.md、index.html、主页更新、Git 提交。
---

# GitHub 项目页面管理

创建和管理 GitHub Pages 项目页面。每次新增项目必须同步更新主页。

## 触发条件

- 新增项目 / 创建项目页面 / 添加到网址
- 更新主页 / 添加项目卡片
- 同步 GitHub / 更新 README

## 工作流

### 创建新项目页面

1. 创建目录结构：`项目名/` + `examples/` + `utils/`（按需）
2. 创建 `README.md`（标准格式）
3. 创建 `index.html`（深色主题 + busuanzi 计数器）
4. 更新主 `README.md`（添加项目条目）
5. 更新主 `index.html`（添加卡片）
6. `git add` + `commit` + `push`

### README.md 标准格式

```markdown
# 项目名称

一句话简介。

## 核心特性

- 特性 1
- 特性 2

## 目录结构

（目录树）

## 快速开始

### 方式一：xxx
### 方式二：xxx

## 参数说明

（表格）

## 依赖

## 开发规范

## 许可证

## 链接
```

### index.html 模板要点

- 深色主题：`--bg1:#0f0c29; --bg2:#302b63; --bg3:#24243e`
- 返回链接：`<a class="back-link" href="../">← 返回主页</a>`
- busuanzi 计数器（必须）：
  ```html
  <div class="page-counter">
    本页被阅读 <span id="busuanzi_value_page_pv">...</span> 次
  </div>
  <script defer src="https://jsd.dusays.com/npm/penndu@17.0.0/bsz.js"></script>
  ```
- 不使用 emoji 图标，纯文字
- 响应式 `max-width` 布局
- 不引入外部 CSS/JS 框架

### 主页更新清单

新增项目页面后必须同步：

- [ ] 主 `README.md` 项目一览表格添加条目
- [ ] 主 `README.md` 目录树添加目录
- [ ] 主 `index.html` 添加卡片（tools 或 guides 分类）
- [ ] 确认所有内部链接有效

## 身份信息清理工作流

当用户要求从公开仓库中移除身份信息时，按以下流程执行：

1. **全局搜索** — 用 grep 在所有 .html/.md/.py/.json/.js 文件中搜索关键词（姓名、专业、学校等）
2. **逐一替换** — 将特定身份描述替换为通用描述：
   - "新能源汽车工程" → 删除或改为通用术语
   - "车辆动力学" → "动力学"
   - "PMSM 电机 FOC" → "电机 FOC"
   - "增程式能量管理" → "能量管理策略"
   - "CarSim 联合仿真" → "联合仿真"
3. **检查配置文件** — SOUL.md、CLAUDE.md 中的用户身份信息也要清理
4. **删除个人文件** — birthday-*.html 等非项目文件直接删除
5. **验证** — `grep -rn "关键词" --include="*.html" --include="*.md" .` 确认无遗漏
6. **提交推送** — commit message 用 `refactor: 去除身份信息`

## 项目隔离模式

当用户说"把 X 和 Y 隔离开来"或"不要联合仿真了"时，执行完全隔离：

1. **移除共享依赖** — 从项目 A 中删除对项目 B 的引用（目录、文件、import）
2. **清理 README** — 移除对方项目的提及
3. **清理 index.html** — 移除对方项目的描述
4. **更新主 README** — 目录树和描述中移除耦合内容
5. **各自独立** — 两个项目都能独立运行，不依赖对方

```bash
# 验证隔离：项目 A 中不应有项目 B 的引用
grep -rn "项目B关键词" 项目A/ --include="*.m" --include="*.md" --include="*.html"
```

## 用户偏好

- **身份保护**：不在公开内容中暴露姓名、专业、学校年级等个人信息
- **描述通用化**：使用通用术语，不用能推断出个人身份的词汇
- **UI 不变**：主页 UI 布局用户满意，只改内容不改样式
- **简洁直接**：不废话，说结果不做总结
- **项目独立**：不同仿真工具（matlab-ai、carsim-ai）完全隔离，不共享依赖

## 更新项目页面视觉元素

当用户要求更新项目页面的图标、logo、banner 等视觉元素时：

1. **获取资源** — 从官方仓库或用户指定位置复制资源文件到项目目录
   ```bash
   # 从官方仓库获取（示例：Hermes Agent logo）
   curl -s "https://raw.githubusercontent.com/NousResearch/hermes-agent/main/website/static/img/logo.png" -o hermes-launcher/hermes-logo.png
   ```

2. **更新 index.html** — 在 hero 区域添加 logo 展示
   ```html
   <!-- HTML：在 hero-badge 前添加 -->
   <img src="hermes-logo.png" alt="Hermes Agent" class="hero-logo">
   
   <!-- CSS：添加样式 -->
   .hero-logo{width:120px;height:120px;margin-bottom:20px;border-radius:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3)}
   ```

3. **更新 README.md** — 在标题下方添加 logo
   ```markdown
   # 项目名称
   
   <img src="hermes-logo.png" alt="Hermes Agent" width="120" style="border-radius:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3)">
   ```

4. **更新主页卡片图标** — 将 emoji 图标替换为实际图片
   ```html
   <!-- 原来：使用 emoji -->
   <div class="card-icon" style="...">⚕</div>
   
   <!-- 改为：使用实际图片 -->
   <div class="card-icon" style="...;padding:4px">
     <img src="hermes-launcher/hermes-logo.png" alt="Hermes" style="width:28px;height:28px;border-radius:6px">
   </div>
   ```

5. **提交推送** — `git add` + `commit` + `push`

### Pitfalls

- 图片路径错误 → 检查相对路径是否正确
- 图片太大 → 压缩或调整尺寸（卡片图标 28x28，hero 区域 120x120）
- 忘记更新主页卡片 → 图标不一致

## 项目重构模式

当用户要求将特定项目重构为通用工具 + 独立示例时：

1. 将原项目重构为通用工具（如 `carsim-ai/`）
2. 将具体示例复制到 `assignments/项目名/` 作为独立作业
3. 作业目录包含完整的 README + 代码，可直接复制到其他电脑使用
4. 更新主页 README.md 目录树添加 `assignments/` 目录

```
project/
├── generic-tool/          通用工具
│   ├── examples/          通用示例脚本
│   ├── utils/             工具函数
│   └── README.md
└── assignments/           作业/示例
    └── specific-case/     独立可运行的示例
        ├── examples/
        ├── utils/
        └── README.md
```

## macOS .app 图标转换

将 PNG 转换为 .icns 格式用于 .app 捆绑包图标。完整步骤见 `references/macos-app-icon-conversion.md`。

```bash
# 快速版：sips 生成各尺寸 → iconutil 合成 .icns → 复制到 .app/Contents/Resources/
```

## 跨页面内容关系管理

当多个页面覆盖相似内容时（如"一键启动器"和"完整指南"），用户会混淆并重复操作。

**触发信号**：用户说"没分清"、"下了两遍"、"重复操作"、"搞混了"。

**问题根因**：两个页面都写了相同的步骤（如安装命令），用户两边都看了一遍，以为是不同的操作。

**解决方案**：

1. **定义页面角色** — 每个页面必须有明确的单一职责：
   - `hermes-launcher` = 已安装用户的快速启动工具（下载 + 确认检查）
   - `hermes-guide` = 从零开始的完整安装教程（安装 + 配置 + 排错）
   - 角色不能重叠：一个页面教"怎么做"，另一个只教"确认是否做好了"

2. **添加交叉引用** — 在重叠区域添加醒目的跳转提示：
   ```html
   <div class="tip info" style="margin-bottom:16px">
     <strong>还没安装？</strong>请先看 <a href="../hermes-guide/" style="color:var(--accent)">完整指南</a> 的安装章节。<br>
     <strong>已经安装过了？</strong>跳过下面，直接下载启动器即可。
   </div>
   ```

3. **替换重复内容为验证步骤** — 不要重复写安装命令，改为"确认已安装"检查：
   ```html
   <!-- 错误：重复安装步骤 -->
   <div class="cmd">curl -fsSL https://...install.sh | bash</div>
   
   <!-- 正确：改为确认检查 -->
   <div class="cmd">hermes --version</div>
   <p>输出版本号说明已安装。未安装？去看 <a href="../完整指南/">完整指南</a></p>
   ```

4. **双向引用** — 完整教程页面也要指向快速启动页面：
   ```html
   <div class="tip green">
     <strong>更简单的方法：</strong><a href="../hermes-launcher/">一键启动器页面</a> 提供了现成的命令，复制粘贴即可。
   </div>
   ```

**检查清单**：
- [ ] 新增页面后，检查是否与已有页面内容重叠
- [ ] 重叠区域是否有明确的交叉引用
- [ ] 用户是否能通过一个页面完成，不需要跳来跳去
- [ ] 角色定义是否清晰（快速启动 vs 完整教程 vs 参考文档）

## 多语言 README 模式

当用户要求 README 支持多国语言时（如"多语言版本"、"国际化"、"i18n"），使用锚点跳转模式：

```markdown
<div align="center">

# 项目名称

**[English](#english)** · **[中文](#中文)** · **[日本語](#日本語)** · **[한국어](#한국어)**

</div>

---

<a id="english"></a>

## 🇬🇧 English
（英文内容）

---

<a id="中文"></a>

## 🇨🇳 中文
（中文内容）

---

<a id="日本語"></a>

## 🇯🇵 日本語
（日文内容）

---

<a id="한국어"></a>

## 🇰🇷 한국어
（韩文内容）
```

**要点**：
- 用 `<a id="xxx">` 锚点 + `#xxx` 链接实现页面内跳转
- 每种语言都要有完整的安装说明和下载链接
- 每种语言的下载链接指向同一个 Release
- 不要用自动翻译，每种语言独立撰写

## GitHub Releases 分发

用户明确要求通过 GitHub Releases 分发软件包，不用 raw.githubusercontent.com。

### 创建 Release 流程

```bash
# 1. 打包
mkdir -p /tmp/release && cp -R skills/xxx /tmp/release/ && cd /tmp/release
zip -r /tmp/xxx-v1.0.zip xxx/

# 2. 创建 Release（需要先 git push）
cd ~/Desktop/lihongwei-cn
gh release create v1.0 /tmp/xxx-v1.0.zip \
  --title "v1.0 - 标题" \
  --notes "## 更新内容\n- 功能1\n- 功能2"

# 3. 清理
rm /tmp/xxx-v1.0.zip && rm -rf /tmp/release
```

### README 中的下载链接格式

```markdown
| 平台 | 下载 |
|------|------|
| macOS | [xxx-macos.zip](https://github.com/OWNER/REPO/releases/download/TAG/xxx-macos.zip) |
| Windows | [xxx-windows.zip](https://github.com/OWNER/REPO/releases/download/TAG/xxx-windows.zip) |
| Linux | [xxx-linux.zip](https://github.com/OWNER/REPO/releases/download/TAG/xxx-linux.zip) |
```

**要点**：
- Release tag 用描述性名称（如 `mundo-v4.0`、`packages`）
- 链接格式：`releases/download/tag/filename`
- 每次版本更新都要创建新 Release
- README 下载链接指向最新 Release

## Skill 部署同步工作流

当更新一个 Skill 时，必须同步更新所有相关位置：

```
SKILL.md 更新
  ↓
1. ~/.hermes/skills/xxx/SKILL.md          ← 主文件
2. global-specs/skills/xxx/SKILL.md       ← 全局规范副本
3. skills/xxx/SKILL.md                    ← 仓库副本（如果有）
4. skills/index.html                      ← 下载链接版本号
5. README.md                              ← 下载链接 + 功能描述
6. GitHub Release                         ← 打包发布
7. git commit + push                      ← 同步
```

**自动化命令**：
```bash
# 同步 SKILL.md 到所有位置
cp ~/.hermes/skills/xxx/SKILL.md global-specs/skills/xxx/SKILL.md
cp ~/.hermes/skills/xxx/SKILL.md skills/xxx/SKILL.md

# 更新版本号（在 skills/index.html 中）
# 更新下载链接（在 README.md 中）

# 提交推送
git add -A && git commit -m "feat: xxx vX.Y" && git push

# 创建 Release
gh release create vX.Y /tmp/xxx-vX.Y.zip --title "xxx vX.Y" --notes "..."
```

## 优化现有内容的红线

**永远不要在优化时删除已有功能和内容。** 这是最容易犯的错误——用"更优化"的版本替换原版，结果丢失了用户精心设计的特征。

### 绝对不能删的东西

- 等级制度、武器库等用户设计的核心特色区块
- 用户确认过的 UI 风格（如金色主题、蒙多口吻）
- 中文优先的结构（用户明确要求中文在最前面）
- 已有的表格、示例、金句等具体内容

### 正确做法

1. **先 `git log` 查看历史** — 了解当前版本的演进过程
2. **先 `git diff` 对比** — 确认改动范围，只增不删
3. **保留所有现有区块** — 在其基础上扩展、优化、补充
4. **新增内容放末尾或新 section** — 不要重组已有结构

### 错误案例

```
用户：优化 README 让更多人看到蒙多
错误：重写整个 README，删除等级制度表格、武器库、蒙多口吻
正确：保留全部原有内容，新增 SEO 关键词、Star History、网站链接
```

## 中英双语页面切换模式

当用户要求项目页面支持中英双语时，使用 `data-lang` 属性 + body 类名切换。

**⚠️ 绝对不要在同一元素上写两个 `class` 属性！** 浏览器只认第一个，第二个被静默忽略。

```html
<!-- 错误：两个 class 属性，class="show" 被忽略 -->
<div class="hero-quote" data-lang="zh" class="show">中文</div>

<!-- 正确：只有一个 class 属性 -->
<div class="hero-quote" data-lang="zh">中文</div>
```

### CSS

```css
/* 默认隐藏英文，中文正常显示（div=block, span=inline） */
[data-lang="en"] { display: none; }

/* body 有 lang-en 类时：显示英文，隐藏中文 */
body.lang-en [data-lang="en"] { display: revert; }
body.lang-en [data-lang="zh"] { display: none; }
```

`display: revert` 恢复元素的默认 display 值（div→block, span→inline），避免 span 被强制变 block。

### JS

```javascript
function switchLang(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(function(b) {
    b.classList.remove('active');
  });
  btn.classList.add('active');
  // 通过 body 类名切换，不操作每个元素
  if (lang === 'en') {
    document.body.classList.add('lang-en');
  } else {
    document.body.classList.remove('lang-en');
  }
}
```

### HTML

```html
<!-- 切换按钮 -->
<div class="lang-switch">
  <button class="lang-btn active" onclick="switchLang('zh',this)">
    <span class="flag">🇨🇳</span> 中文
  </button>
  <button class="lang-btn" onclick="switchLang('en',this)">
    <span class="flag">🇬🇧</span> English
  </button>
</div>

<!-- 内容区块：不需要 class="show" -->
<div data-lang="zh">中文内容...</div>
<div data-lang="en">English content...</div>

<!-- span 也一样 -->
<button class="copy-btn">
  📋 <span data-lang="zh">复制</span><span data-lang="en">Copy</span>
</button>
```

**要点**：
- 不需要在每个中文元素上加 `class="show"`，CSS 默认就显示中文
- 通过 `body.lang-en` 一个类名控制所有元素，性能更好
- `display: revert` 保证 span 不会变成 block
- 所有用户可见文字都要有 `data-lang` 属性
- 两种语言都要有完整的安装、下载、示例内容

## README 加入网站链接模式

当项目有独立网站页面且内容比 README 更详细时，在 README 的下载区块后添加：

```markdown
### 🌐 更多详细内容

**[👉 进入官方网站查看完整介绍（中英双语）](https://xxx.github.io/xxx/)**

包含：特性A · 特性B · 特性C · 安装教程 · 示例
```

英文段落对应加：
```markdown
### 🌐 Full Documentation

**[👉 Visit the official website for the complete guide (CN/EN)](https://xxx.github.io/xxx/)**
```

## Pitfalls

- 忘记加 busuanzi 计数器 → 页面没有访问统计
- 忘记更新主页 → 新项目在首页看不到
- README 格式不一致 → 用户会纠正
- **优化时删除已有内容（等级制度、武器库等）→ 用户要求还原。永远只增不删**
- **重写 README 时丢失中文优先结构 → 用户纠正。中文内容必须在最前面**
- **中英切换页面忘记给按钮文字加 data-lang → 切换语言后按钮文字不变**
- **中英切换页面默认中文没加 class="show" → 页面打开时中文内容不显示** — 这是旧方案的坑，改用 body 类名切换则不需要 class="show"
- **HTML 元素写了两个 class 属性 → 浏览器只认第一个，第二个被静默丢弃。如 class="hero-quote" data-lang="zh" class="show" 中 class="show" 完全无效。永远只用一个 class 属性**
- 硬编码密钥 → 安全红线，从环境变量读取
- 提交 `.env`、`__pycache__`、`.DS_Store` → 加入 .gitignore
- 重构后忘记删除旧的具体示例代码 → 目录冗余
- assignments 目录没有独立 README → 用户无法提取使用
- **多个页面重复相同步骤 → 用户跟着两边各做一遍，导致重复操作。用交叉引用替代重复内容**
- **只更新了 SKILL.md 没有同步到 global-specs、skills 页面、README、Release → 版本不一致**
- **用 raw.githubusercontent.com 链接做下载 → 用户要求用 GitHub Releases**
- **多语言 README 用机器翻译 → 每种语言应独立撰写**
