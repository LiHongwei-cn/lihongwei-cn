---
name: miniprogram-ai-display
description: "Beautifully render AI-generated markdown text in WeChat mini-programs — WXS parser, section cards, inline bold."
trigger:
  - keywords: [小程序, AI反馈, AI分析, markdown渲染, WXS, 润色, 美化, AI文字]
  - context: "用户要求美化小程序中 AI 返回的文字内容"
---

# 小程序 AI 文字美化渲染

微信小程序中 `rich-text` 组件支持有限，AI 返回的 markdown（emoji 标题 + `**粗体**`）直接当纯文本展示会很单调。以下是将纯文本 AI 反馈渲染为美观分区卡片的完整方案。

## 核心思路

1. 创建 WXS 模块解析 AI 文本 → 结构化数据 `{sections: [{icon, title, lines: [{parts: [{text, bold}]}]}]}`
2. WXML 中用 `<wxs>` 引用模块，`<block wx:for>` 遍历 sections 渲染卡片
3. 每个 section 有独立的 icon + title 头部，content 用圆点列表 + 粗体高亮

## 第一步：WXS 解析器

创建 `utils/md.wxs`：

```javascript
function parseSections(text) {
  if (!text) return { sections: [] }
  var sections = []
  var lines = text.split('\n')
  var current = null

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i]
    // 匹配 emoji 开头的标题行：📈 **标题**
    var headerMatch = line.match(/^([\u{1F300}-\u{1FAFF}...]+)\s*\*\*(.+?)\*\*/u)
    if (headerMatch) {
      if (current) sections.push(current)
      current = { icon: headerMatch[1], title: headerMatch[2], lines: [] }
    } else if (current) {
      var trimmed = line.trim()
      if (trimmed) current.lines.push(parseInline(trimmed))
    }
  }
  if (current) sections.push(current)
  return { sections: sections }
}

function parseInline(text) {
  var parts = []
  var remaining = text
  while (remaining.length > 0) {
    var boldIdx = remaining.indexOf('**')
    if (boldIdx === -1) { parts.push({ text: remaining, bold: false }); break }
    if (boldIdx > 0) parts.push({ text: remaining.substring(0, boldIdx), bold: false })
    remaining = remaining.substring(boldIdx + 2)
    var endIdx = remaining.indexOf('**')
    if (endIdx === -1) { parts.push({ text: remaining, bold: false }); break }
    parts.push({ text: remaining.substring(0, endIdx), bold: true })
    remaining = remaining.substring(endIdx + 2)
  }
  return { parts: parts }
}

module.exports = { parseSections: parseSections, parseInline: parseInline }
```

## 第二步：WXML 模板

在需要使用解析器的页面顶部引用 WXS，然后用 block 遍历：

```xml
<wxs src="../../utils/md.wxs" module="md" />

<!-- AI 分析区域 -->
<view wx:if="{{aiText}}">
  <!-- 头部卡片 -->
  <view class="card ai-card-header">
    <view class="ai-header-icon">🤖</view>
    <view class="ai-header-text">
      <text class="ai-header-title">AI 分析</text>
      <text class="ai-header-sub">基于数据智能生成</text>
    </view>
  </view>

  <!-- 分区卡片 -->
  <block wx:for="{{md.parseSections(aiText).sections}}" wx:key="index">
    <view class="card ai-section">
      <view class="ai-section-head">
        <text class="ai-section-icon">{{item.icon}}</text>
        <text class="ai-section-title">{{item.title}}</text>
      </view>
      <view class="ai-section-body">
        <block wx:for="{{item.lines}}" wx:for-item="line" wx:key="idx">
          <view class="ai-line">
            <text class="ai-dot">·</text>
            <view class="ai-line-parts">
              <block wx:for="{{line.parts}}" wx:for-item="part" wx:key="idx2">
                <text class="{{part.bold ? 'ai-bold' : ''}}">{{part.text}}</text>
              </block>
            </view>
          </view>
        </block>
      </view>
    </view>
  </block>
</view>
```

## 第三步：WXSS 样式

分区卡片使用级联样式：首个 section 继承 header 圆角，中间无缝，末个 section 恢复底圆角：

```css
.ai-card-header {
  display: flex; align-items: center; gap: 20rpx;
  margin-bottom: 0;
  border-bottom-left-radius: 0; border-bottom-right-radius: 0;
}

.ai-header-icon {
  width: 80rpx; height: 80rpx; line-height: 80rpx; text-align: center;
  font-size: 40rpx;
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  border-radius: 20rpx; flex-shrink: 0;
}

.ai-section {
  margin-top: 0; border-radius: 0;
  padding: 28rpx 32rpx 24rpx;
  border-top: 1rpx solid #f0f0f0;
}
.ai-section:last-child {
  border-bottom-left-radius: var(--radius);
  border-bottom-right-radius: var(--radius);
  margin-bottom: 24rpx;
}

.ai-section-head { display: flex; align-items: center; gap: 12rpx; margin-bottom: 18rpx; }
.ai-section-icon { font-size: 36rpx; }
.ai-section-title { font-size: 30rpx; font-weight: 700; }

.ai-line { display: flex; align-items: flex-start; margin-bottom: 12rpx; }
.ai-dot { color: var(--primary); font-weight: 700; font-size: 28rpx; margin-right: 10rpx; }
.ai-line-parts { font-size: 28rpx; line-height: 1.7; color: var(--text-secondary); flex: 1; }
.ai-bold { font-weight: 700; color: var(--text); }
```

## 适用场景

- AI 周报/分析结果展示（如血压分析报告）
- AI 对话回复渲染
- 任何后端返回 emoji + markdown 格式文本需要美化展示的场景

## 注意事项

- WXS 文件必须用 `<wxs src="..." module="md" />` 在页面顶部引用，不能在 component 的 json 中声明
- WXS 的 regex 支持不如 JS 完整，emoji 匹配需要显式列出 Unicode 范围
- 如果 AI 返回格式变化（如改用 `### 标题`），需相应调整 headerMatch 正则
