---
name: web-ui-design
description: "高级感 Web 前端 UI 设计资源库。覆盖组件库、CSS 框架、动画库、设计系统。"
category: design
tags: [web, ui, css, react, tailwind, design]
---

# Web 前端 UI 设计资源库

## 一、当前最火组件库

### 1. shadcn/ui ⭐ 80k+
- 链接：https://github.com/shadcn-ui/ui
- 特点：复制粘贴组件，不是 npm 包，完全可控
- 技术栈：React + Tailwind + Radix UI
- 安装：

```bash
npx shadcn@latest init
npx shadcn@latest add button
```

- 设计风格：极简、无多余装饰、黑白为主
- 适合：现代 Web 应用、Dashboard、SaaS

### 2. Aceternity UI ⭐ 20k+
- 链接：https://github.com/aceternity/aceternity-ui
- 特点：动画组件库，光晕/粒子/3D 特效
- 技术栈：React + Framer Motion + Tailwind
- 精选组件：
  - Background Gradient Animation（渐变背景动画）
  - Bento Grid（苹果风格网格布局）
  - Card Hover Effect（卡片悬停特效）
  - Text Generate Effect（文字生成动画）
  - Wavy Background（波浪背景）

### 3. Magic UI ⭐ 15k+
- 链接：https://github.com/magicuidesign/magicui
- 特点：类似 Aceternity，更轻量
- 精选组件：
  - Marquee（无限滚动）
  - Animated Beam（动画光束）
  - Globe（3D 地球）
  - Number Ticker（数字滚动）
  - Shimmer Button（闪烁按钮）

---

## 二、CSS 框架

### 4. Tailwind CSS ⭐ 85k+
- 链接：https://github.com/tailwindlabs/tailwindcss
- 特点：原子化 CSS，当前主流
- 安装：

```bash
npm install -D tailwindcss
npx tailwindcss init
```

- 配合 shadcn/ui 使用效果最佳

### 5. DaisyUI ⭐ 35k+
- 链接：https://github.com/saadeghi/daisyui
- 特点：Tailwind 组件库，主题丰富
- 安装：

```bash
npm install daisyui
```

- 主题：light, dark, cupcake, bumblebee, emerald, corporate, synthwave, retro, cyberpunk, valentine, halloween, garden, forest, aqua, lofi, pastel, fantasy, wireframe, black, luxury, dracula, cmyk, autumn, business, acid, lemonade, night, coffee, winter, dim, nord, sunset, caramellatte, silk

### 6. Float UI ⭐ 3k+
- 链接：https://github.com/nicepkg/floatui
- 特点：开源替代 shadcn，设计感强
- 技术栈：React + Tailwind

---

## 三、动画库

### 7. Framer Motion ⭐ 25k+
- 链接：https://github.com/framer/motion
- 特点：React 动画库，流畅丝滑
- 安装：

```bash
npm install framer-motion
```

- 常用动画：

```jsx
import { motion } from "framer-motion"

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  内容
</motion.div>
```

### 8. AutoAnimate ⭐ 12k+
- 链接：https://github.com/formkit/auto-animate
- 特点：零配置动画，一行代码搞定
- 安装：

```bash
npm install @formkit/auto-animate
```

### 9. GSAP ⭐ 20k+
- 链接：https://github.com/greensock/GSAP
- 特点：专业级动画库，性能最佳
- 适合：复杂动画、滚动动画

---

## 四、设计系统

### 10. Radix UI ⭐ 16k+
- 链接：https://github.com/radix-ui/primitives
- 特点：无样式原语，完全可控
- shadcn/ui 的底层依赖

### 11. Headless UI ⭐ 25k+
- 链接：https://github.com/tailwindlabs/headlessui
- 特点：Tailwind 官方无样式组件
- 适合：配合 Tailwind 自定义样式

---

## 五、Landing Page 模板

### 12. Tailwind Templates
- 链接：https://tailwindui.com/templates
- 特点：官方模板，设计精美
- 价格：付费但值得

### 13. HyperUI ⭐ 8k+
- 链接：https://github.com/markmead/hyperui
- 特点：免费 Tailwind 组件，商用友好
- 分类：Marketing, E-commerce, Application

### 14. Tailblocks ⭐ 8k+
- 链接：https://github.com/mertJF/tailblocks
- 特点：60+ 预设区块，即插即用

---

## 六、图标库

### 15. Lucide Icons ⭐ 12k+
- 链接：https://github.com/lucide-icons/lucide
- 特点：shadcn/ui 默认图标，极简风格
- 安装：`npm install lucide-react`

### 16. Heroicons ⭐ 22k+
- 链接：https://github.com/tailwindlabs/heroicons
- 特点：Tailwind 官方图标

### 17. Phosphor Icons ⭐ 1.5k+
- 链接：https://github.com/phosphor-icons/react
- 特点：6 种粗细，风格统一

---

## 七、字体推荐

### 中文
- **思源黑体**（Noto Sans CJK）：Google + Adobe 合作，免费商用
- **思源宋体**（Noto Serif CJK）：学术/正式场合
- **霞鹜文楷**（LXGW WenKai）：开源楷体，优雅文艺

### 英文
- **Inter**：现代无衬线，UI 首选
- **JetBrains Mono**：代码字体，程序员最爱
- **Playfair Display**：衬线字体，高级感

---

## 八、最佳实践组合

### 现代 Web 应用
```
React + Tailwind + shadcn/ui + Framer Motion + Lucide Icons
```

### Landing Page
```
Next.js + Tailwind + Aceternity UI + Magic UI
```

### Dashboard
```
React + Tailwind + shadcn/ui + Recharts + Radix UI
```

### 个人主页
```
Astro + Tailwind + 自定义组件 + GSAP 动画
```

---

## 九、设计原则

1. **留白**：足够的间距让内容呼吸
2. **层次**：用大小、粗细、颜色区分信息层级
3. **一致**：统一的间距、圆角、阴影
4. **克制**：动画要适度，不要过度设计
5. **可读**：字号 ≥ 14px，行高 1.5-1.8