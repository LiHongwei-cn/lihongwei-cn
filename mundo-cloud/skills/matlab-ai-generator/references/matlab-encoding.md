# MATLAB 文件编码规范（macOS + Windows 跨平台）

## 问题

Windows MATLAB R2016b 保存 .m 文件时使用 GBK 编码（ISO-8859），在 macOS 上显示为乱码。
macOS 上创建的 UTF-8 文件在 Windows MATLAB R2016b 上可能显示乱码。

## 解决方案

**所有 .m 文件统一使用 UTF-8 编码。**

Windows MATLAB R2016b 在中文系统区域设置下可以正确读取 UTF-8 文件。

## 验证方法

```bash
# 检查文件编码
file matlab/examples/*.m

# 正确结果：Unicode text, UTF-8 text
# 错误结果：ISO-8859 text（需要重新保存为 UTF-8）
```

## 修复方法

如果文件是 GBK 编码：
1. 用 Claude Code 重写整个文件（会自动使用 UTF-8）
2. 或用 iconv 转换：`iconv -f GBK -t UTF-8 input.m > output.m`

## 强制规则

- 新建 .m 文件必须是 UTF-8
- 修改已有 .m 文件后验证编码未变
- 中文注释、中文标签、中文 fprintf 输出——全部用 UTF-8
- 代码变量名保持英文
