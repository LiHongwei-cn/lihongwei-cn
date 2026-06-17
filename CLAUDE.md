# CLAUDE.md — Claude Code 项目记忆

> 此文件由 Hermes Agent 自动维护，同时 Claude Code 也可直接编辑。
> 编辑后内容会反向同步到 Hermes 记忆系统。

---

## 用户身份

- 黄鹏，南京航空航天大学金城学院，新能源汽车工程 2023-2027
- 求职方向：AI应用开发（首选）/ 汽车电子（次选）
- 证书：AutoCAD + Creo 高级、低压电工证、C1 驾照、校级奖学金
- 已投：大丁科技(DING AUTO)实习，上海，汽车电子HIL/ADAS

## 回复风格（红线）

- 简洁直接，不废话，不写"总结一下""以上就是"
- 内容谦虚客观，不用"最强/最好/碾压"
- 对比表格用"基础/部分/—"，不用贬低性词汇
- 不泄露个人信息（真名、学校、专业），对外用化名
- 代码注释只写"为什么"，不写"是什么"
- 不创建 README/CHANGELOG/计划文档（除非明确要求）
- 不使用 emoji（除非明确要求）

## 技术栈

- MATLAB R2016b（跨平台兼容，.m 文件 UTF-8，禁止 2017+ 函数）
- CarSim 2019.0 + Simulink 联合仿真
- Python 3.11/3.12
- HTML/CSS（纯手写，深色主题，响应式）
- 微信小程序
- Git/GitHub

## 项目结构

```
~/Desktop/lihongwei-cn/          # GitHub 仓库主目录
├── matlab/                       # MATLAB 仿真
├── bot/                          # Telegram Bot
├── bp-monitor/                   # 血压监测小程序
├── tools/                        # 启动脚本
├── docs/                         # 论文/报告
├── index.html                    # GitHub Pages 主页
├── global-specs/                 # 全局规范
└── starter-kit/                  # 通用模板
```

## 已知坑（必须避开）

- MATLAB R2016b：`%%` 长分隔线会导致图表垃圾文字
- MATLAB .m 文件必须 UTF-8，不用 GBK（macOS 会乱码）
- prompt_toolkit：ANSI 码显示乱码用 `HTML()` 代替
- pywebview 在 macOS .app 中窗口不显示
- `read_file` 返回格式是 "行号|内容"，编辑时需先剥离行号
- GitHub Pages 从 `gh-pages` 分支构建，不是 `main`
- `mimo-v2.5-pro-ultraspeed` 在 API 上不存在（返回 400）

## Git 规范

- Commit 格式：`<type>: <description>`（feat/fix/refactor/docs/chore）
- 不提交 `.env`、密钥、`__pycache__`、`.DS_Store`
- 每次代码修改后自动 add + commit + push

## 代码规范

- 变量/函数：camelCase
- 布尔值：is/has/should/can 前缀
- 常量：UPPER_SNAKE_CASE
- 函数 <50 行，文件 <800 行
- 三个相似代码行 > 一个不必要的抽象
- 不可变数据：创建新对象，不修改已有对象
- 深层嵌套用提前返回展平

## 关键项目记忆

### Mundo Agent
- 路径：~/.hermes/mundo-agent/
- 版本：v2.2.6，54模块/30+模型
- 七处同步：SKILL.md + README.md + index.html + GitHub Release + ~/.hermes/skills/ + Info.plist + 启动脚本
- 蒙多UI：金色#D4AF37 + 深色#0a0a0f，厌恶紫色白色

### 留白
- 路径：~/Applications/留白/
- 定位："倾诉的陌生人"，禁暴露心理医生身份

### Boss直聘自动化
- 路径：~/Desktop/.boss-auto/
- 启动：cd ~/Desktop/.boss-auto && ./start_browser.sh
- 端口 8765

## Claude Code 使用说明

当你需要记住新的重要信息时，在本文件对应章节追加即可。
当你发现用户纠正了你的行为，更新"回复风格"或"已知坑"章节。
保持本文件精简，不超过 200 行。
