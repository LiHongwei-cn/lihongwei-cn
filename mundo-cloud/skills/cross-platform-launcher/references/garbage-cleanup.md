# macOS 系统垃圾清理

用户说"清理垃圾""清除残留""清理缓存"时执行此流程。

## 检查阶段

```bash
# 缓存目录大小
du -sh ~/Library/Caches
du -sh ~/Library/Caches/pip
du -sh ~/Library/Caches/Homebrew
du -sh ~/Library/Caches/uv
du -sh ~/.npm

# 用户项目垃圾
find ~/Desktop -name ".DS_Store" | wc -l
find ~/Desktop -name "__pycache__" | wc -l
find ~ -name "*.pyc" -not -path "*/.*" | wc -l

# 下载目录安装包残留
find ~/Downloads -name "*.dmg" -o -name "*.pkg" -o -name "*.tar.gz"

# 工具缓存
du -sh ~/.hermes
du -sh ~/.claude
```

## 清理阶段

按风险从低到高执行：

```bash
# 1. 用户项目垃圾（安全）
find ~/Desktop -name ".DS_Store" -delete
find ~/Desktop -name "__pycache__" -type d -exec rm -rf {} +

# 2. 包管理器缓存
pip cache purge
brew cleanup
rm -rf ~/Library/Caches/uv
rm -rf ~/.npm/_cacache

# 3. Python 系统缓存
rm -rf ~/Library/Caches/com.apple/python

# 4. 下载目录安装包
find ~/Downloads \( -name "*.dmg" -o -name "*.pkg" -o -name "*.tar.gz" \) -delete

# 5. 工具日志/缓存
find ~/.hermes/logs -name "*.log" -mtime +7 -delete
rm -rf ~/.hermes/cache
rm -rf ~/.claude/cache

# 6. 回收站
rm -rf ~/.Trash/*

# 7. Git 仓库未跟踪文件（需用户确认）
cd ~/project && git clean -fd
```

## 注意事项

- **不要删除** `~/Library/Caches/com.apple.python` 以外的系统级 Python 缓存（/System、/Library 下的）
- **不要删除** `~/.hermes` 下的 config.yaml、.env、skills/、memory/（这些是配置和持久数据）
- **不要删除** `~/.claude` 下的 CLAUDE.md、skills/（配置文件）
- `git clean -fd` 会删除未跟踪文件，执行前用 `git clean -fdn`（dry-run）预览
- 5555 个 .pyc 文件如果全在系统 Python 目录（如 ~/Library/Python、CommandLineTools），属于系统缓存，不建议删除
