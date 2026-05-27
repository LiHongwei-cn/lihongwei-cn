# MATLAB 项目合并指南

当两个相关项目需要合并为一个统一项目时使用此流程。区别于删除（见 project-deletion-checklist.md），合并需要保留有价值的内容。

## 合并决策矩阵

| 情况 | 处理方式 |
|------|---------|
| 项目 A 有价值，项目 B 易报错 | 保留 A，删除 B，将 B 中有价值的部分迁移到 A |
| 两个项目功能重叠 | 合并到一个新的统一项目 |
| 项目 A 是核心，项目 B 是扩展 | 将 B 作为 A 的子模块/可选功能 |

## 合并步骤

### Step 1: 审计两个项目

```bash
# 列出两个项目的所有文件
ls -laR project-a/ project-b/
# 找出所有引用这两个项目的位置
grep -rn "project-a\|project-b" --include="*.html" --include="*.md" --include="*.command" --include="*.bat" . | grep -v ".git/"
```

### Step 2: 确定合并策略

- **保留哪个目录名**：通常保留更通用的那个
- **哪些文件迁移**：从被合并项目中挑选有价值的文件
- **哪些文件删除**：易报错的、重复的、过时的
- **HTML 页面合并**：将两个页面的功能卡片合并为一个

### Step 3: 执行合并

```bash
# 1. 删除不需要的项目
rm -rf project-b/

# 2. 将有价值文件迁移到保留项目
mv project-b/useful-file.m project-a/

# 3. 重命名启动脚本（如果需要）
mv tools/project-a.command tools/unified-name.command
mv tools/project-a.bat tools/unified-name.bat

# 4. 更新启动脚本内部引用
sed -i '' 's/project-a/unified-name/g' tools/unified-name.command
```

### Step 4: 更新所有引用

| 引用位置 | 操作 |
|----------|------|
| `index.html` | 删除旧卡片，添加新合并卡片 |
| `matlab/README.md` | 更新目录树，添加合并后的内容 |
| `matlab/index.html` | 更新项目页面，添加新功能卡片 |
| `tools/*.command` | 更新路径引用 |
| `tools/*.bat` | 更新路径引用 |
| `CLAUDE.md` | 更新目录树和技术栈 |
| `global-specs/` | 同步 CLAUDE.md 变更 |
| `starter-kit/` | 如果包含被合并项目的文件，同步更新 |

### Step 5: 验证

```bash
# 验证零残留
grep -rn "project-b" --include="*.html" --include="*.md" --include="*.m" --include="*.command" --include="*.bat" . | grep -v ".git/" | wc -l
# 必须输出 0

# 验证新引用完整
grep -rn "unified-name" --include="*.html" --include="*.md" . | head -10
```

## 真实案例（2026-05-26）

将 `matlab-ai/` 和 `carsim-ai/` 合并为统一的 `matlab/` 项目：

**保留的**：`matlab/`（核心仿真代码 + utils + examples）
**删除的**：`carsim-ai/`（CarSim 工具，易报错）、`matlab-ai/`（仅 HTML 页面）
**迁移的**：
- `matlab-ai/index.html` → 合并到 `matlab/index.html`（新增仿真卡片）
- `carsim-ai/examples/` → 删除（作业示例）
- `tools/matlab-ai.command` → 重命名为 `tools/matlab.command`
- `tools/carsim-ai.*` → 删除

**引用更新**：19 个文件中的 CarSim 引用全部清除
**结果**：主页两张卡片合并为一张「MATLAB 仿真工具包」
