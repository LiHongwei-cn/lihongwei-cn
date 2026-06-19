---
name: ppt-templates
description: "高级感 PPT 制作工具和模板集合。支持 Markdown 转 PPT、AI 生成、LaTeX Beamer 等方案。"
category: design
tags: [ppt, presentation, slides, markdown, latex]
---

# PPT 制作工具与模板

## 一、开发者首选（Markdown → PPT）

### 1. Slidev ⭐ 35k+
- 链接：https://github.com/slidevjs/slidev
- 特点：Vue 驱动，代码高亮，LaTeX 公式，动画流畅
- 安装：`npm init slidev@latest`
- 主题推荐：seriph（米色+衬线字体，极简美学）
- 适合：技术分享、组会、答辩

```bash
npm init slidev@latest
# 选择 seriph 主题
# 编辑 slides.md 即可
# 导出 PDF: slidev export
```

### 2. Marp ⭐ 12k+
- 链接：https://github.com/marp-team/marp
- 特点：最简单的 Markdown 转 PPT，VS Code 插件支持
- 安装：`npm install -g @marp-team/marp-cli`
- CSS 主题：https://github.com/marp-team/marp/tree/main/themes

```bash
marp slides.md --pdf --theme gaia
```

### 3. Reveal.js ⭐ 67k+
- 链接：https://github.com/hakimel/reveal.js
- 特点：最流行的 HTML 演示框架，3D 过渡，无限画布
- 适合：需要精细控制的演示

---

## 二、学术/专业风格

### 4. LaTeX Beamer
- 模板库：https://github.com/matze/mtheme
- 特点：学术界标配，排版精准，极简专业
- 主题推荐：metropolis（现代极简）

```latex
\documentclass{beamer}
\usetheme{metropolis}
\title{标题}
\author{作者}
\date{\today}
\begin{document}
\maketitle
\begin{frame}{内容}
  正文
\end{frame}
\end{document}
```

### 5. Typst ⭐ 40k+
- 链接：https://github.com/typst/typst
- 特点：现代排版系统，比 LaTeX 更易用
- 安装：`brew install typst`

---

## 三、AI 生成 PPT

### 6. Gamma.app（商业）
- 链接：https://gamma.app
- 特点：AI 生成 PPT，设计感极强，支持中文
- 适合：快速生成高质量演示

### 7. Tome（商业）
- 链接：https://tome.app
- 特点：AI 叙事工具，自动生成精美页面
- 适合：故事化演示

---

## 四、精美主题推荐

### Slidev 主题
- **seriph**：米色背景 + 衬线字体，极简美学
- **apple-basic**：苹果风格，简洁现代
- **dracula**：暗色主题，程序员最爱
- **default**：默认主题，百搭

### Reveal.js 主题
- **black**：经典暗色
- **white**：简洁亮色
- **league**：深蓝专业
- **night**：深紫优雅

---

## 五、导出与分享

### Slidev 导出
```bash
# 导出 PDF
slidev export slides.md
# 导出 PNG 图片
slidev export --format png slides.md
# 导出多个 PDF（按点击）
slidev export --per-slide slides.md
```

### Marp 导出
```bash
# 导出 PDF
marp slides.md --pdf
# 导出 HTML
marp slides.md --html
# 导出 PPTX
marp slides.md --pptx
```

---

## 六、最佳实践

1. **技术分享**：Slidev + seriph 主题
2. **学术答辩**：LaTeX Beamer + metropolis
3. **快速演示**：Marp + VS Code
4. **精美展示**：Reveal.js + 自定义 CSS
5. **AI 辅助**：Gamma.app

---

## 七、相关资源

- Slidev 主题市场：https://github.com/topics/slidev-theme
- Marp 主题：https://github.com/topics/marp-theme
- Beamer 模板：https://github.com/topics/beamer-template
- Reveal.js 插件：https://github.com/topics/revealjs-plugin