# 蒙多同步工作流

## 完整同步流程

每次蒙多版本更新时，必须执行以下同步步骤：

### 1. 更新本地 SKILL.md
```bash
# 编辑 ~/.hermes/skills/mundo/SKILL.md
```

### 2. 同步到 global-specs
```bash
cp ~/.hermes/skills/mundo/SKILL.md ~/Desktop/lihongwei-cn/global-specs/skills/蒙多/SKILL.md
cp ~/.hermes/skills/mundo/SKILL.md ~/Desktop/lihongwei-cn/skills/mundo/SKILL.md
```

### 3. 创建 Release 包
```bash
mkdir -p /tmp/mundo-release
cp -R ~/Desktop/lihongwei-cn/skills/mundo /tmp/mundo-release/
cd /tmp/mundo-release
zip -r /tmp/mundo-vX.Y.zip mundo/
rm -rf /tmp/mundo-release
```

### 4. 更新 README.md
- 四国语言版本（中/英/日/韩）
- 更新下载链接指向新版本
- 更新版本号

### 5. 更新 skills/index.html
- 更新描述文本
- 更新下载链接版本号

### 6. 提交并推送
```bash
cd ~/Desktop/lihongwei-cn
git add -A
git commit -m "feat: MUNDO vX.Y - 描述"
git push
```

### 7. 创建 GitHub Release
```bash
cd ~/Desktop/lihongwei-cn
gh release create mundo-vX.Y /tmp/mundo-vX.Y.zip \
  --title "MUNDO vX.Y - 标题" \
  --notes "## 内容..."
```

### 8. 清理临时文件
```bash
rm /tmp/mundo-vX.Y.zip
```

## 版本命名规则

- 主要版本（架构改变）：v1.0, v2.0, v3.0...
- 次要版本（功能增加）：v1.1, v1.2...
- 补丁版本（修复优化）：v1.0.1, v1.0.2...

## 同步检查清单

- [ ] 本地 SKILL.md 已更新
- [ ] global-specs 已同步
- [ ] skills/mundo 已同步
- [ ] README.md 四国语言已更新
- [ ] skills/index.html 已更新
- [ ] Release 包已创建
- [ ] GitHub 已提交推送
- [ ] Release 已创建
- [ ] 临时文件已清理
