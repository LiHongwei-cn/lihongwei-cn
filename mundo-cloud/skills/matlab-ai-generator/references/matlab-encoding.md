# MATLAB 文件编码规范

## 问题

Windows MATLAB R2016b 默认使用系统编码（GBK/CP936）保存含中文的 .m 文件。在 macOS 上显示为 ISO-8859，中文内容乱码。

## 验证方法

```bash
file xxx.m
# 期望: "Unicode text, UTF-8 text"
# 异常: "ISO-8859 text" (GBK 编码)
```

## 修复方法

1. 用 Claude Code 重写文件内容（自动 UTF-8）
2. 或用 iconv 转码: `iconv -f GBK -t UTF-8 input.m > output.m`
3. 验证: `file output.m` 应显示 UTF-8

## 批量修复

```bash
# 检查所有 .m 文件编码
file *.m | grep -v UTF-8

# 批量转码 (需安装 iconv)
for f in *.m; do
  if file "$f" | grep -q ISO-8859; then
    iconv -f GBK -t UTF-8 "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  fi
done
```

## 注意事项

- Claude Code 重写文件时自动使用 UTF-8，是最安全的修复方式
- 大批量重写（>5 文件）需分批执行，避免超时
- MATLAB R2016b 在 Windows 上读取 UTF-8 文件时，如果系统区域设置为中文，可以正常显示
