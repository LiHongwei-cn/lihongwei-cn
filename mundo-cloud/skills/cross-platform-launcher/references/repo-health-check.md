# GitHub 仓库健康检查清单

检查项目仓库是否有损坏、缺失、权限问题。适用于定期巡检或用户说"检查仓库"。

## 检查项

### 1. 不应提交的文件
```bash
find . -name ".DS_Store" -o -name "__pycache__" -o -name "*.pyc" \
  -o -name "node_modules" -o -name ".env" | grep -v ".git"
```

### 2. 缺失的 LICENSE
```bash
# README 中引用了 LICENSE 但文件不存在
grep -q 'href="LICENSE"' README.md && [ ! -f LICENSE ] && echo "MISSING LICENSE"
# 修复：创建 MIT LICENSE 文件
```

### 3. Shell 脚本执行权限
```bash
find . -name "*.sh" -o -name "*.command" | while read f; do
  [ ! -x "$f" ] && echo "NOT EXECUTABLE: $f"
done
# 修复：chmod +x <file>
```

### 4. 空文件
```bash
find . -not -path "./.git/*" -type f -empty
```

### 5. 主页链接完整性
```bash
# 提取主页所有相对链接，检查目标是否存在
grep -o 'href="[^"]*/"' index.html | sed 's/href="//;s/"//' | while read dir; do
  [ ! -f "${dir}index.html" ] && echo "MISSING: ${dir}index.html"
done
```

### 6. HTML 有效性
```bash
find . -name "*.html" -not -path "./.git/*" | while read f; do
  grep -q "<!DOCTYPE html>" "$f" || echo "INVALID: $f"
done
```

### 7. 图片完整性
```bash
find . -name "*.jpg" -o -name "*.png" | grep -v ".git" | while read f; do
  size=$(stat -f%z "$f")  # macOS
  [ "$size" -lt 100 ] && echo "SUSPICIOUS: $f ($size bytes)"
done
```

### 8. README 链接检查
```bash
# 检查 README 中的相对链接
grep -o 'href="[^"]*"' README.md | grep -v "http" | grep -v "#" | while read link; do
  target=$(echo "$link" | sed 's/href="//;s/"//')
  [ ! -f "$target" ] && echo "BROKEN: $link"
done
```

## 修复后必须

- git add + commit + push
- 验证 GitHub Pages 是否同步（curl 检查关键页面）
