# 完整项目介绍页模板

参照 `matlab-tool/index.html`，这是 LiHongwei GitHub Pages 所有项目页面的标准格式。

## HTML 结构（从上到下）

```
容器 .container (max-width:900px)
├── 返回链接 .back-link → "../"
├── Hero .hero
│   ├── 徽章 .hero-badge
│   ├── 标题 h1（渐变文字）
│   └── 描述 p
├── 下载区 .download-box
│   ├── 图标 + 标题 + 描述
│   ├── 按钮组 .download-buttons（主按钮 .btn-primary + 备用 .btn-secondary）
│   └── 文件信息 .file-info
├── 工作流程 .section
│   ├── 标题 .section-title + .num
│   └── 卡片网格 .feature-grid > .feature-card × 4
├── 步骤教程 .section（可多个）
│   ├── 标题
│   └── 步骤列表 .step-list > .step-item（CSS counter 自动编号）
│       ├── 标题 h3
│       ├── 段落 p
│       ├── 代码块 .cmd
│       └── 提示 .tip
├── 详情卡片 .section
│   ├── 标题
│   └── 卡片网格 .sim-grid > .sim-card
│       ├── 头部 .sim-header（图标 .sim-icon + 名称 .sim-name）
│       ├── 参数 .sim-params
│       ├── 描述 .sim-desc
│       ├── 输出 .sim-outputs
│       └── 命令 .sim-cmd
├── 兼容性 .section
│   └── .feature-grid > .feature-card × 4
├── 文件列表 .section
│   └── .file-group > .file-group-label + .file-list > .file-row
├── 计数器 .page-counter
│   └── <span id="busuanzi_page_pv">...</span>
└── 底部 .footer
    └── GitHub 链接 + 协议
```

## CSS 变量标准

```css
:root{
  --bg1:#0f0c29;
  --bg2:#302b63;
  --bg3:#24243e;
  --card:rgba(255,255,255,0.05);
  --border:rgba(255,255,255,0.08);
  --text:#e8e8e8;
  --dim:rgba(255,255,255,0.45);
  --accent:#6c8cff;
  --green:#4ade80;
  --orange:#fb923c;
}
```

## 关键 CSS 类

| 类 | 用途 |
|----|------|
| `.step-list` | 步骤容器，`counter-reset:step` |
| `.step-item` | 步骤项，`::before` 用 `counter-increment:step` 显示编号 |
| `.feature-grid` | 四列特性卡片网格 |
| `.sim-grid` | 详情卡片网格，min 260px |
| `.file-group` / `.file-list` / `.file-row` | 文件列表 |
| `.tip` / `.tip.info` / `.tip.warn` | 提示框 |

## 必含元素清单

- [ ] busuanzi 页面计数器（`.page-counter`）
- [ ] busuanzi 脚本 `<script defer src="https://jsd.dusays.com/npm/penndu@17.0.0/bsz.js"></script>`
- [ ] 返回链接 `<a class="back-link" href="../">← 返回主页</a>`
- [ ] Footer 含 GitHub 链接 + "基于 MIT 协议开源"
- [ ] 渐变 Hero 标题（`-webkit-background-clip:text`）
- [ ] 响应式 `@media(max-width:640px)` 断点
- [ ] 字体栈含中文回退：`-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif`

## 主页卡片格式

新增项目后，在 `index.html` 对应分类区添加：

```html
<a class="card" href="project-name/" data-id="project-name">
  <div class="card-icon" style="background:linear-gradient(135deg,#色1,#色2)">图标</div>
  <div class="card-body">
    <div class="card-title">项目名称</div>
    <div class="card-desc">一句话描述 · 关键词 · 关键词</div>
  </div>
  <span class="card-badge" data-views="..."></span>
</a>
```

## 数据统计

- busuanzi 使用 `page_pv` 统计单页访问
- 主页使用 `site_pv` 统计全站访问
- CDN: `https://jsd.dusays.com/npm/penndu@17.0.0/bsz.js`
