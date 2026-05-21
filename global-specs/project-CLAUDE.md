# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 关键信息

- GitHub 仓库：`https://github.com/<your-org>/<your-repo>`
- 部署地址：`https://<your-org>.github.io/<your-repo>/`
- 外部服务：API Key 等从环境变量读取，详见 `.env.example`

## 项目概览

简述项目用途和技术栈（2-3 句话）。

## 技术栈

- 语言/框架
- 构建工具
- 部署平台

## 目录架构

```
.
├── src/             源代码
├── docs/            文档
├── tools/           工具脚本
├── CLAUDE.md        项目规范（本文件）
└── README.md
```

## 代码质量

- 文件命名：`kebab-case` / `snake_case`（选定后全局一致）
- 函数单一职责，< 50 行（Python）/ < 200 行（MATLAB）
- 复用优先：公共函数不重复定义
- 参数验证：公共函数入口检查参数合法性

## Git 规范

- commit message: `<type>: <description>`（feat, fix, refactor, docs, chore）
- 先 diff 再 commit，不提交 `.env`、密钥、`__pycache__`

## 安全红线

- 绝不硬编码密钥（API Key、Token、密码）
- 所有密钥从环境变量读取
- `.env` 不提交到 Git
- 外部输入在显示/执行前验证

## 常用命令

```bash
# 开发
npm run dev

# 构建
npm run build

# 测试
npm test
```

## 跨平台要求

- 所有工具、脚本、教程必须同时覆盖 Windows 和 macOS
- 新增脚本时同时提供 .bat（Win）和 .sh/.command（Mac）

## 任务收尾

每次代码修改后：
1. `git add` + `git commit` + `git push`
2. 检查部署地址内容是否与代码一致
3. 确认无密钥泄露到仓库
