---
name: resume-builder
description: "高级感简历制作工具和模板集合。覆盖 JSON Resume、LaTeX、Markdown、在线编辑器等方案。"
category: design
tags: [resume, cv, latex, json, template]
---

# 简历制作工具与模板

## 一、开源最强

### 1. Reactive Resume ⭐ 25k+
- 链接：https://github.com/AmruthPillworking/Reactive-Resume
- 特点：最强开源简历编辑器，实时预览，多模板
- 功能：
  - 拖拽式编辑
  - 20+ 精美模板
  - 实时预览
  - 导出 PDF/JSON
  - 多语言支持
  - 隐私优先（数据本地存储）
- 部署：

```bash
git clone https://github.com/AmruthPillworking/Reactive-Resume.git
cd Reactive-Resume
docker compose up -d
```

### 2. JSON Resume ⭐ 2k+
- 链接：https://github.com/jsonresume
- 特点：JSON 标准 + 主题生态，一键生成
- 标准格式：

```json
{
  "basics": {
    "name": "姓名",
    "label": "职位",
    "email": "email@example.com",
    "phone": "138-0000-0000",
    "url": "https://example.com",
    "summary": "个人简介",
    "location": {
      "city": "城市",
      "countryCode": "CN"
    },
    "profiles": [
      {
        "network": "GitHub",
        "username": "username",
        "url": "https://github.com/username"
      }
    ]
  },
  "work": [...],
  "education": [...],
  "skills": [...],
  "projects": [...],
  "certificates": [...]
}
```

- 主题推荐：
  - `jsonresume-theme-elegant`：优雅简洁
  - `jsonresume-theme-kendall`：现代专业
  - `jsonresume-theme-even`：极简美学
  - `jsonresume-theme-stackoverflow`：技术风格

- 使用：

```bash
npm install -g resume-cli
resume init
resume export resume.html --theme elegant
```

---

## 二、LaTeX 简历模板

### 3. Deedy Resume ⭐ 3k+
- 链接：https://github.com/deedy/Deedy-Resume
- 特点：经典双栏 LaTeX 简历，技术风格
- 编译：`xelatex resume.tex`

### 4. AltaCV ⭐ 2k+
- 链接：https://github.com/liantze/AltaCV
- 特点：现代 LaTeX 简历，侧边栏设计
- 特色：
  - 时间线设计
  - 技能图表
  - 图标集成
  - 深色/浅色主题

### 5. Awesome CV ⭐ 2k+
- 链接：https://github.com/posquit0/Awesome-CV
- 特点：极简专业，学术界最爱
- 特色：
  - 清晰的分区
  - 图标联系方式
  - 多语言支持

### 6. Modern CV ⭐ 2k+
- 链接：https://github.com/xdanaux/moderncv
- 特点：经典现代风格，多种样式
- 样式：casual, classic, banking, oldstyle, fancy

---

## 三、Markdown 简历

### 7. markdown-cv ⭐ 2k+
- 链接：https://github.com/elipapa/markdown-cv
- 特点：Markdown 写简历，极简美学
- 使用：

```markdown
# 姓名

职位 | 邮箱 | 电话

## 教育背景

**学校** - 专业 (2020-2024)

## 工作经历

**公司** - 职位 (2024-至今)
- 成就1
- 成就2

## 技能

- 技能1, 技能2, 技能3
```

### 8. GitProfile ⭐ 3k+
- 链接：https://github.com/arifszn/gitprofile
- 特点：GitHub 个人主页 + 简历生成
- 自动从 GitHub 获取项目信息

---

## 四、在线工具

### 9. FlowCV（商业）
- 链接：https://flowcv.com
- 特点：设计感最强的在线简历工具
- 优势：
  - 实时预览
  - 20+ 精美模板
  - AI 辅助写作
  - 导出 PDF/Word
  - 免费使用

### 10. Novoresume（商业）
- 链接：https://novoresume.com
- 特点：专业简历模板，ATS 友好
- 优势：
  - 专业设计
  - ATS 优化
  - 多模板
  - 内容建议

### 11. Resume.io（商业）
- 链接：https://resume.io
- 特点：简洁专业，快速创建
- 优势：
  - 15+ 模板
  - 预填内容
  - 导出 PDF
  - 免费基础版

---

## 五、设计原则

### 排版
1. **一页原则**：应届生/实习生简历不超过一页
2. **留白充足**：上下左右至少 20mm 边距
3. **对齐统一**：所有元素左对齐或两端对齐
4. **层次分明**：用大小、粗细、颜色区分信息层级

### 字体
- **中文**：思源黑体、微软雅黑、苹方
- **英文**：Inter、Roboto、Open Sans
- **字号**：姓名 24-28px，标题 14-16px，正文 11-13px

### 颜色
- **主色**：深蓝 #1a1a2e 或 #2563eb
- **强调色**：一个即可，不要多色混搭
- **背景**：纯白 #fff，不要渐变

### 内容
1. **STAR 法则**：Situation-Task-Action-Result
2. **量化数据**：用数字代替形容词
3. **动词开头**：设计、开发、优化、实现
4. **相关优先**：与目标岗位相关的放前面

---

## 六、最佳实践

### 学生/应届生
```
Reactive Resume + 简洁模板
或
JSON Resume + elegant 主题
```

### 技术岗位
```
LaTeX (Deedy Resume 或 Awesome CV)
或
Markdown + markdown-cv
```

### 设计岗位
```
FlowCV 或 Novoresume（设计感强）
```

### 学术申请
```
LaTeX Awesome CV 或 Modern CV
```

---

## 七、ATS 优化

ATS（Applicant Tracking System）是简历筛选系统，需要注意：

1. **文件格式**：PDF 或 Word，不要图片格式
2. **字体**：使用常见字体，避免特殊字体
3. **关键词**：包含 JD 中的关键词
4. **简洁布局**：避免复杂表格、图片、图标
5. **标准分区**：教育、工作、技能、项目

---

## 八、相关资源

- JSON Resume 主题：https://jsonresume.org/themes
- LaTeX 简历模板：https://www.latextemplates.com/cat/curricula-vitae
- 简历写作指南：https://www.resume.com/blog/
- ATS 测试工具：https://www.jobscan.co/