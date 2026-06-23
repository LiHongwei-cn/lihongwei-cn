<div align="center">

# 李宏伟的个人项目主页

**MATLAB/Simulink 仿真 · Python · 微信小程序 · AI Agent · 工具链**

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-lihongwei--cn.github.io-blue)](https://lihongwei-cn.github.io/lihongwei-cn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 项目概览

| 项目 | 说明 |
|------|------|
| [MUNDO Agent](https://github.com/LiHongwei-cn/mundo-agent) | v2.2.9 · 独立 AI 智能体 · 安全加固 · 代码重构 · 220 测试 · 12 种安全检测 |
| [MATLAB 仿真工具包](matlab/) | 车辆动力学、电机控制、能量管理（R2016b 兼容） |
| [家庭血压监测小程序](bp-monitor/) | FastAPI + SQLite + DeepSeek 后端 |
| [Telegram Bot](bot/) | DeepSeek 驱动的智能助手 |
| [MATLAB 工具包安装页面](matlab-tool/) | 一键安装 MATLAB 工具包 |
| [Claude Code 教程](claude-code-tutorial/) | 入门指南 |
| [VPN 自建指南](vpn-guide/) | 免费 VPN 搭建教程 |
| [系统优化](win-optimize/) | Windows/macOS 优化 |
| [通用模板](starter-kit/) | 开源模板 |

## 技术栈

- **MATLAB/Simulink** R2016b（车辆动力学、电机控制 FOC、能量管理）
- **Python** 3.12 + FastAPI
- **微信小程序** WXML/WXSS/JS
- **AI Agent** MUNDO Agent（独立 AI 智能体框架）
- **HTML/CSS** GitHub Pages 静态页面

## MUNDO Agent

MUNDO 是一个独立的 AI 智能体框架，具有以下特性：

- **30+ AI 模型支持**：DeepSeek、MiMo、Qwen、Claude、GPT-4o、Gemini 等
- **安全加固**：五层纵深防御 + 12 种危险命令检测 + 速率限制 + 输出消毒覆盖敏感格式
- **向量检索 RAG**：ChromaDB + BM25 + 语义哈希三路融合，API Embedding / 本地哈希双模式
- **评估框架**：多维度量化（任务完成率、步骤效率、工具准确率），内置 10+ 评估用例
- **MCP 互操作**：Client + Server 双向协议，蒙多能力通过标准 MCP 对外暴露
- **可观测性**：结构化日志、分布式追踪（OpenTelemetry 兼容）、指标采集
- **三层记忆系统**：短期/中期/长期记忆，SQLite + FTS5 + WAL 优化
- **反射循环引擎**：THINK → EXECUTE → REFLECT → REPAIR 四阶段
- **代码质量**：220 单元测试、模块化架构、类型注解、零冗余转发层
- **集体意识**：一个蒙多学到，所有蒙多都会
- **自我进化**：每次使用都让蒙多更强大
- **多 Agent 委托**：支持 Claude Code、Hermes Agent、Codex

### 快速开始

```bash
# 下载最新版
gh release download v2.2.9 -R LiHongwei-cn/mundo-agent -p "mundo-v2.2.9-macos.zip"

# 解压
unzip mundo-v2.2.9-macos.zip -d ~/.hermes/mundo-agent

# 运行
python3 ~/.hermes/mundo-agent/mundo.py
```

## 网站

👉 [lihongwei-cn.github.io/lihongwei-cn](https://lihongwei-cn.github.io/lihongwei-cn/)

## License

MIT License - 完全免费开源
