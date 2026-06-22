---
name: design-resources
description: "高级感设计资源库。覆盖色彩系统、字体搭配、图标库、设计工具、灵感来源。"
category: design
tags: [design, color, font, icon, inspiration]
---

# 设计资源库

## 一、色彩系统

### 深色主题（高级感首选）

```css
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: #1a1a2e;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --accent: #d4af37;      /* 金色 */
  --accent-hover: #f0d060;
  --border: #2a2a3e;
}
```

### 浅色主题（专业感）

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-card: #ffffff;
  --text-primary: #1a1a2e;
  --text-secondary: #6b7280;
  --accent: #2563eb;      /* 蓝色 */
  --accent-hover: #1d4ed8;
  --border: #e5e7eb;
}
```

### 配色工具
- **Coolors**：https://coolors.co — 随机生成配色方案
- **ColorHunt**：https://colorhunt.co — 精选配色方案
- **Realtime Colors**：https://realtimecolors.com — 实时预览配色
- **Tailwind Colors**：https://tailwindcss.com/docs/customizing-colors

---

## 二、字体搭配

### 中文字体
- **思源黑体**（Noto Sans CJK）：免费商用，现代无衬线
- **思源宋体**（Noto Serif CJK）：学术/正式场合
- **霞鹜文楷**（LXGW WenKai）：开源楷体，优雅文艺
- **得意黑**（Smiley Sans）：开源黑体，设计感强

### 英文字体
- **Inter**：现代无衬线，UI 首选
- **JetBrains Mono**：代码字体，程序员最爱
- **Playfair Display**：衬线字体，高级感
- **Space Grotesk**：几何无衬线，科技感

### 搭配方案
1. **现代简洁**：Inter + 思源黑体
2. **学术专业**：Playfair Display + 思源宋体
3. **科技感**：Space Grotesk + 得意黑
4. **文艺清新**：LXGW WenKai + Space Grotesk

### 字体加载

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, sans-serif;
}
```

---

## 三、图标库

### 1. Lucide Icons ⭐ 12k+
- 链接：https://github.com/lucide-icons/lucide
- 特点：shadcn/ui 默认图标，极简风格
- 安装：`npm install lucide-react`

### 2. Heroicons ⭐ 22k+
- 链接：https://github.com/tailwindlabs/heroicons
- 特点：Tailwind 官方图标

### 3. Phosphor Icons ⭐ 1.5k+
- 链接：https://github.com/phosphor-icons/react
- 特点：6 种粗细，风格统一

### 4. Tabler Icons ⭐ 18k+
- 链接：https://github.com/tabler/tabler-icons
- 特点：4000+ 图标，免费商用

### 5. Iconify ⭐ 3k+
- 链接：https://github.com/iconify/iconify
- 特点：100+ 图标库统一接口

---

## 四、设计工具

### 免费
- **Figma**：https://figma.com — 最流行的在线设计工具
- **Penpot**：https://penpot.app — 开源 Figma 替代
- **Excalidraw**：https://excalidraw.com — 手绘风格白板
- **tldraw**：https://tldraw.com — 极简白板

### 付费
- **Sketch**：macOS 专用，UI 设计标杆
- **Adobe XD**：Adobe 生态
- **Framer**：设计 + 原型 + 代码

---

## 五、灵感来源

### 设计作品
- **Dribbble**：https://dribbble.com — 设计师社区
- **Behance**：https://behance.net — Adobe 设计社区
- **Awwwards**：https://awwwards.com — 网页设计奖项

### 开源设计
- **UIverse**：https://uiverse.io — 开源 UI 组件
- **Hover.dev**：https://hover.dev — React 动画组件
- **Motion Primitives**：https://motion-primitives.com — 动画组件

### 设计系统
- **Material Design**：https://m3.material.io — Google 设计系统
- **Human Interface**：https://developer.apple.com/design/human-interface-guidelines — Apple 设计指南
- **Fluent UI**：https://fluent2.microsoft.design — Microsoft 设计系统

---

## 六、设计原则

### 视觉层次
1. **大小**：重要内容更大
2. **粗细**：标题粗体，正文常规
3. **颜色**：强调色突出重点
4. **间距**：相关内容靠近，无关内容远离

### 留白
- **内容间距**：至少 8px
- **卡片间距**：16-24px
- **区块间距**：32-48px
- **页面边距**：至少 24px

### 一致性
- **圆角**：统一使用 4px/8px/12px
- **阴影**：统一使用一种阴影
- **动画**：统一时长 200-300ms
- **颜色**：只用 2-3 种主色

---

## 七、响应式设计

### 断点
```css
/* 移动端 */
@media (max-width: 640px) { ... }

/* 平板 */
@media (min-width: 641px) and (max-width: 1024px) { ... }

/* 桌面 */
@media (min-width: 1025px) { ... }
```

### 最佳实践
1. **移动优先**：先写移动端样式
2. **流式布局**：使用 % 和 vw/vh
3. **弹性图片**：max-width: 100%
4. **媒体查询**：按需添加桌面样式

---

## 八、性能优化

### 图片
- **格式**：WebP > PNG > JPG
- **尺寸**：按需加载，不要过大
- **懒加载**：`loading="lazy"`

### 字体
- **子集化**：只加载需要的字符
- **预加载**：`<link rel="preload">`
- **显示策略**：`font-display: swap`

### CSS
- **压缩**：生产环境压缩 CSS
- **关键 CSS**：内联首屏 CSS
- **避免嵌套**：减少选择器复杂度