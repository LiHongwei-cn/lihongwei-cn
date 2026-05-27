# macOS .app 图标设置

将 PNG 图标应用到自建 .app（如 ~/Applications/hermes.app）。

## 完整流程

```bash
# 1. 生成所有尺寸的 iconset
mkdir -p /tmp/AppName.iconset
sips -z 16 16     icon.png --out /tmp/AppName.iconset/icon_16x16.png
sips -z 32 32     icon.png --out /tmp/AppName.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out /tmp/AppName.iconset/icon_32x32.png
sips -z 64 64     icon.png --out /tmp/AppName.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out /tmp/AppName.iconset/icon_128x128.png
sips -z 256 256   icon.png --out /tmp/AppName.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out /tmp/AppName.iconset/icon_256x256.png
sips -z 512 512   icon.png --out /tmp/AppName.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out /tmp/AppName.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out /tmp/AppName.iconset/icon_512x512@2x.png

# 2. 转换为 .icns
iconutil -c icns /tmp/AppName.iconset -o /tmp/AppName.icns

# 3. 替换 .app 中的图标
cp /tmp/AppName.icns ~/Applications/AppName.app/Contents/Resources/AppName.icns

# 4. 触发 macOS 图标缓存刷新
touch ~/Applications/AppName.app

# 5. 清理临时文件
rm -rf /tmp/AppName.iconset /tmp/AppName.icns
```

## 要点

- 源 PNG 建议 1024x1024 或更大，sips 会自动缩放
- Info.plist 中 `CFBundleIconFile` 值必须与 .icns 文件名（不含扩展名）一致
- `touch .app` 后 Dock 图标可能仍不刷新，需右键从 Dock 移除再重新拖入
- iconset 必须包含 10 个尺寸（16 到 512@2x），缺一不可
