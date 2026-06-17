# CLAUDE.md — Claude Code 项目记忆

> 此文件由 Hermes Agent 自动维护，Claude Code 也可直接编辑。
> 编辑后内容会反向同步到 Hermes 记忆系统。

---

## 用户身份

- 黄鹏，南京航空航天大学金城学院，新能源汽车工程 2023-2027
- 求职方向：AI应用开发（首选）/ 汽车电子（次选）
- 证书：AutoCAD + Creo 高级、低压电工证、C1 驾照、校级奖学金
- 已投：大丁科技(DING AUTO)实习，上海，汽车电子HIL/ADAS，联系孔经理 will.kong@dingauto.cn

## 回复风格（红线）

- 简洁直接，不废话，不写"总结一下""以上就是"
- 内容谦虚客观，不用"最强/最好/碾压"
- 对比表格用"基础/部分/—"，不用贬低性词汇
- 不泄露个人信息（真名、学校、专业），对外用化名
- 代码注释只写"为什么"，不写"是什么"
- 不创建 README/CHANGELOG/计划文档（除非明确要求）
- 不使用 emoji（除非明确要求）
- 学习资料要自包含，不想去其他网址看

## 网站

- 主页：https://lihongwei-cn.github.io/lihongwei-cn/
- GitHub：https://github.com/LiHongwei-cn/lihongwei-cn
- 深色主题，纯 HTML/CSS，响应式，无框架

## 技术栈

- MATLAB R2016b（.m 文件 UTF-8，禁止 2017+ 函数，禁止 eval/feval）
- CarSim 2019.0 + Simulink 联合仿真
- Python 3.11/3.12
- HTML/CSS（纯手写，深色主题，响应式）
- 微信小程序（微信云开发 + DeepSeek AI）
- Git/GitHub

---

## 全部项目清单

### 核心项目（独立仓库/大型项目）

| 项目 | 路径 | 说明 |
|------|------|------|
| MUNDO Agent | ~/.hermes/mundo-agent/ | 独立AI智能体，v2.2.6，54模块/30+模型，七处同步 |
| 留白 | ~/Applications/留白/ | 情感陪伴小程序，"倾诉的陌生人"，内容感知回复 |
| Boss直聘自动化 | ~/Desktop/.boss-auto/ | HTTP Server + 浏览器方案，端口8765，AI接mimo |

### 仓库内项目（~/Desktop/lihongwei-cn/）

| 目录 | 页面 | 说明 |
|------|------|------|
| matlab/ | matlab/index.html | MATLAB仿真工具包，车辆动力学/电机控制/能量管理，R2016b兼容 |
| matlab-tool/ | matlab-tool/index.html | MATLAB工具包安装页面 |
| bp-monitor/ | - | 家庭血压监测微信小程序，微信云开发+DeepSeek AI |
| mundo-agent/ | mundo-agent/index.html | MUNDO Agent 项目页面（GitHub Pages 展示） |
| mundo-cloud/ | - | MUNDO 云同步相关 |
| ccs-launcher/ | ccs-launcher/index.html | Claude Code 一键启动器，Win/Mac双击即用 |
| desktop-launcher/ | desktop-launcher/index.html | Claude Code 桌面快捷启动 |
| hermes-launcher/ | hermes-launcher/index.html | Hermes Agent 一键启动器 |
| hermes-guide/ | hermes-guide/index.html | Hermes Agent 完整指南（安装/配置/踩坑） |
| claude-code-tutorial/ | claude-code-tutorial/index.html | Claude Code 完整指南（安装/DeepSeek接入/Skill） |
| telegram-bot/ | telegram-bot/index.html | 蒙多 Telegram Bot 页面 |
| vpn-guide/ | vpn-guide/index.html | 免费VPN自建指南，Cloudflare零成本搭建 |
| win-optimize/ | win-optimize/index.html | Win/Mac系统优化教程 |
| ai-anatomy/ | ai-anatomy/index.html | AI剖析 — 用人体构造理解AI模型/Agent/Skill |
| skill-store/ | skill-store/index.html | 蒙多Skill云仓库，206个Skill |
| skills/ | skills/index.html | Skills市场页面 |
| starter-kit/ | - | MATLAB AI仿真代码生成通用模板 |
| global-specs/ | global-specs/index.html | 全局规范部署包 |
| bot/ | - | Telegram Bot（旧版Python，已被Hermes Gateway替代） |
| docs/ | - | 论文/实验报告 |
| tools/ | - | 启动脚本和自动化工具 |
| resume/ | - | 简历相关 |
| github-trending/ | - | GitHub趋势相关 |
| references/ | - | 参考资料 |
| assets/ | - | 静态资源 |

### 本地应用（~/Applications/）

| 应用 | 说明 |
|------|------|
| MUNDO.app | MUNDO Agent 桌面启动器 |
| Hermes-Agent.app | Hermes Agent 桌面启动器 |
| Claude Code.app | Claude Code 桌面启动器 |
| Claude Code URL Handler.app | Claude Code URL 处理器 |

---

## 已知坑（必须避开）

- MATLAB R2016b：`%%` 长分隔线会导致图表垃圾文字
- MATLAB .m 文件必须 UTF-8，不用 GBK（macOS 会乱码）
- prompt_toolkit：ANSI 码显示乱码用 `HTML()` 代替
- pywebview 在 macOS .app 中窗口不显示，用 HTTP 服务器+浏览器替代
- `read_file` 返回格式是 "行号|内容"，编辑时需先剥离行号
- GitHub Pages 从 `gh-pages` 分支构建，不是 `main`
- `mimo-v2.5-pro-ultraspeed` 在 API 上不存在（返回 400）
- mimo API base_url: token-plan-cn.xiaomimimo.com

## Git 规范

- Commit 格式：`<type>: <description>`（feat/fix/refactor/docs/chore）
- 不提交 `.env`、密钥、`__pycache__`、`.DS_Store`
- 每次代码修改后自动 add + commit + push
- GitHub Pages 部署：push main 后需手动合并到 gh-pages

## 代码规范

- 变量/函数：camelCase
- 布尔值：is/has/should/can 前缀
- 常量：UPPER_SNAKE_CASE
- 函数 <50 行，文件 <800 行
- 三个相似代码行 > 一个不必要的抽象
- 不可变数据：创建新对象，不修改已有对象
- 深层嵌套用提前返回展平

## 关键历史决策

- Mundo Agent 是独立项目，不是 Hermes 的 skill
- 留白定位"倾诉的陌生人"，禁暴露心理医生身份
- 蒙多UI铁律：金色#D4AF37 + 深色#0a0a0f，厌恶紫色白色
- .app 启动器在 macOS 有问题，用 .command 脚本最可靠
- Boss直聘自动化用 HTTP Server + 浏览器方案（pywebview 在 .app 中不显示）
- GitHub Pages 从 gh-pages 分支构建，每次 push main 后需手动合并

---

## 项目发布规范（五处同步）

每次项目内容更新后，必须同步以下 5 个位置：

| # | 位置 | 说明 |
|---|------|------|
| 1 | `<project>/index.html` | 项目展示页（GitHub Pages） |
| 2 | `<project>/README.md` | 项目 README |
| 3 | 根目录 `index.html` | 个人主页项目卡片 |
| 4 | 根目录 `README.md` | 仓库项目表格 |
| 5 | GitHub Release | `gh release create v<X.Y.Z>` |

版本号格式：`vMAJOR.MINOR.PATCH`

发布流程：
1. 更新版本号 → version.txt
2. 更新项目页面 + README
3. 更新主页卡片 + 根 README
4. git add + commit + push main
5. 合并到 gh-pages 并 push
6. gh release create 创建发行包

## Claude Code 使用说明

当你需要记住新的重要信息时，在本文件对应章节追加即可。
当你发现用户纠正了你的行为，更新"回复风格"或"已知坑"章节。
保持本文件精简，不超过 300 行。
