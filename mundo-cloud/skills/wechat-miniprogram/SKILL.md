---
name: wechat-miniprogram
description: "微信小程序开发、调试、审核拒绝修复。云函数认证、页面加载失败诊断、app.json 配置、WXML/WXSS 常见坑。"
trigger:
  - keywords: [小程序, 微信小程序, 微信云开发, 云函数, miniprogram, wx.cloud, 审核被拒, 页面打不开, 登录失败]
  - context: "用户的小程序审核被拒、页面报错、登录异常、云函数调用失败"
---

# 微信小程序开发与调试

覆盖微信小程序的常见开发问题诊断、审核拒绝修复、云开发认证模式。

## 审核拒绝快速诊断清单

小程序审核被拒最常见的两个原因：

### 1. 页面打不开 / 白屏

**根因排查顺序：**

1. **空 JS 文件** — 最常见。检查页面 `require()` 的模块是否为 0 字节
   ```bash
   find miniprogram/ -name "*.js" -empty
   ```
2. **JS 模块导出缺失** — 检查 `module.exports` 是否正确
3. **JSON 配置错误** — `app.json` 重复 key、页面路径错误、组件路径不存在
4. **组件未注册** — 页面 `.json` 中 `usingComponents` 路径是否正确
5. **CSS 变量未定义** — 使用了 `var(--xxx)` 但 `:root` 或 `page` 中未声明

**诊断命令：**
```bash
# 检查空文件
find miniprogram/ -name "*.js" -empty
find miniprogram/ -name "*.json" -empty

# 检查 app.json 重复 key
cat miniprogram/app.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>&1

# 检查 require 引用的文件是否存在
grep -rn "require(" miniprogram/pages/ | while IFS= read -r line; do
  file=$(echo "$line" | grep -oP "require\('([^']+)'\)" | sed "s/require('//;s/')//")
  dir=$(echo "$line" | cut -d: -f1 | xargs dirname)
  [ -n "$file" ] && [ ! -f "$dir/$file" ] && echo "MISSING: $dir/$file"
done
```

### 2. 微信登录失败

**核心概念：云函数不需要 wx.login() 的 code**

微信云开发中，云函数通过 `cloud.getWXContext()` 自动获取用户 `OPENID`，不需要前端传 code。

**正确模式：**
```javascript
// 前端 auth.js — 直接调用云函数，不需要 wx.login()
const cloud = require('./cloud.js');

function login() {
  return cloud.login().then(function (data) {
    var app = getApp();
    app.globalData.userInfo = data.user;
    return data.user;
  });
}
```

```javascript
// 云函数 — 从 context 获取 OPENID
exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext();
  if (!OPENID) {
    return { error: '未能获取用户身份' };
  }
  // 用 OPENID 查询/创建用户...
};
```

**错误模式（不要用）：**
```javascript
// ❌ 错误：发送空 code
api.post('/auth/login', { code: '' })

// ❌ 错误：wx.login() 获取 code 传给云函数（云函数不需要）
wx.login({ success: (res) => { cloud.login({ code: res.code }) } })
```

## 云函数架构模式

### 统一入口模式（推荐）

一个云函数 `api` 处理所有请求，通过 `action` 参数分发：

```javascript
// cloudfunctions/api/index.js
exports.main = async (event, context) => {
  const { action, data } = event;
  const { OPENID } = cloud.getWXContext();

  switch (action) {
    case 'login': return await handleLogin(OPENID);
    case 'addReading': return await handleAddReading(OPENID, data);
    case 'getReadings': return await handleGetReadings(OPENID, data);
    // ...
    default: return { error: '未知操作: ' + action };
  }
};
```

### 前端调用封装

```javascript
// utils/cloud.js — 统一云函数调用 + 错误诊断
function callFunction(action, data) {
  return new Promise(function (resolve, reject) {
    wx.cloud.callFunction({
      name: 'api',
      data: { action: action, data: data || {} }
    }).then(function (res) {
      if (res.result && res.result.error) {
        reject(new Error(res.result.error));
        return;
      }
      resolve(res.result || {});
    }).catch(function (err) {
      var msg = diagnoseError(err);
      wx.showToast({ title: msg, icon: 'none', duration: 3000 });
      reject(new Error(msg));
    });
  });
}
```

### 错误诊断函数

```javascript
function diagnoseError(err) {
  var s = String((err && err.errMsg) || '');
  if (s.indexOf('timeout') !== -1) return '请求超时，请检查网络连接';
  if (s.indexOf('-501000') !== -1) return '云函数未部署，请先上传云函数';
  if (s.indexOf('not enable') !== -1) return '云开发环境未开通';
  if (s.indexOf('-1') !== -1) return '云开发服务异常，请检查环境ID';
  return '云函数调用失败，请检查云开发配置';
}
```

## app.json 常见问题

```json
{
  "pages": ["pages/index/index", ...],
  "cloud": true,                    // 只写一次！
  "window": { ... },
  "style": "v2",
  "lazyCodeLoading": "requiredComponents",
  "sitemapLocation": "sitemap.json"
}
```

**易错点：**
- `"cloud": true` 重复声明（JSON 允许但语义混乱）
- `pages` 数组中路径拼写错误
- `sitemapLocation` 指向的文件不存在
- `"style": "v2"` 启用了新组件样式但 WXSS 未适配

## app.js 启动流程

```javascript
App({
  globalData: { userInfo: null },

  onLaunch() {
    wx.cloud.init({ env: 'your-env-id', traceUser: true });
    this.checkLogin();
  },

  checkLogin() {
    // 静默登录，失败不阻塞页面
    auth.login().catch(function () {});
  },

  clearLogin() {
    this.globalData.userInfo = null;
  }
});
```

**注意：** `checkLogin` 失败不应阻塞页面加载。页面的 `onShow` 中应再次检查登录状态。

## CSS 变量一致性

在 `app.wxss` 的 `page` 选择器中定义所有全局变量：

```css
page {
  --primary: #2c7a4f;
  --danger: #d93025;
  --text: #1a1a1a;
  --text-secondary: #666666;
  --text-light: #999999;
  --bg: #f5f5f5;
  --card-bg: #ffffff;
  --border: #e0e0e0;
  --radius: 16rpx;
}
```

**易错点：** 页面 WXSS 中使用了 `var(--text-primary)` 但 app.wxss 定义的是 `var(--text)`。变量名不匹配导致颜色不生效。

## TabBar 底部导航

### 添加 TabBar 后的致命坑：navigateTo → switchTab

**这是最常见的坑。** 添加 tabBar 后，原来用 `wx.navigateTo` 跳转到 tabBar 页面的代码**全部失效**（静默失败，不报错）。

```javascript
// ❌ 错误：navigateTo 不能跳转 tabBar 页面
wx.navigateTo({ url: '/pages/record/record' });

// ✅ 正确：switchTab 跳转 tabBar 页面
wx.switchTab({ url: '/pages/record/record' });
```

**排查方法：** 添加 tabBar 后，全局搜索所有 `navigateTo`，把指向 tabBar 页面的全部改为 `switchTab`。

### TabBar 图标生成

TabBar 图标必须是 PNG 文件（81×81px）。用 Python 生成占位图标：

```python
import struct, zlib

def create_icon(path, r, g, b, size=81):
    raw = b''
    for y in range(size):
        raw += b'\x00'
        for x in range(size):
            cx, cy = size//2, size//2
            dist = ((x-cx)**2 + (y-cy)**2) ** 0.5
            if dist < size//2 - 2:
                raw += bytes([r, g, b, 255])
            else:
                raw += bytes([0, 0, 0, 0])
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

# 灰色（未选中）+ 绿色（选中）
create_icon('assets/tab-home.png', 153, 153, 153)
create_icon('assets/tab-home-active.png', 44, 122, 79)
```

### TabBar 配置

```json
{
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#2c7a4f",
    "backgroundColor": "#ffffff",
    "borderStyle": "black",
    "list": [
      { "pagePath": "pages/index/index", "text": "首页",
        "iconPath": "assets/tab-home.png", "selectedIconPath": "assets/tab-home-active.png" }
    ]
  }
}
```

## 下拉刷新

必须在**两个地方**同时配置才能生效：

```json
// 页面 xxx.json
{ "enablePullDownRefresh": true, "backgroundTextStyle": "dark" }
```

```javascript
// 页面 xxx.js
onPullDownRefresh() {
  this.loadData().finally(() => wx.stopPullDownRefresh());
}
```

## 输入防抖

表单输入频繁触发 setData 和验证，用防抖优化：

```javascript
let validateTimer = null;

onSystolicInput(e) {
  this.setData({ systolic: e.detail.value });
  if (validateTimer) clearTimeout(validateTimer);
  validateTimer = setTimeout(() => this.validateSys(), 300);
},
```

## onShow 数据加载 + Promise 返回

页面用 `onShow` 而非 `onLoad` 加载数据，这样从其他页面返回时数据自动刷新。
`loadData` 必须返回 Promise，这样 `onPullDownRefresh` 可以等待它完成：

```javascript
onShow() {
  this.loadData();
},

onPullDownRefresh() {
  this.loadData().finally(() => wx.stopPullDownRefresh());
},

loadData() {
  this.setData({ loading: true });
  return cloud.getReadings({ page: 1, limit: 20 })
    .then((data) => { this.setData({ readings: data.items }); })
    .catch(() => { wx.showToast({ title: '加载失败', icon: 'none' }); })
    .finally(() => { this.setData({ loading: false }); });
},
```

**关键点：** `loadData` 必须 `return` Promise 链，否则 `onPullDownRefresh` 的 `.finally()` 不会等待数据加载完成就停止刷新动画。

## 预登录模式

App.js 启动时预登录，减少首屏等待：

```javascript
App({
  globalData: { userInfo: null, loginPromise: null },

  onLaunch() {
    wx.cloud.init({ env: 'your-env-id', traceUser: true });
    this.globalData.loginPromise = auth.login().catch(err => {
      console.warn('[app] pre-login failed:', err.message);
    });
  }
});
```

页面中可 `await app.globalData.loginPromise` 等待预登录完成。

## 云函数超时重试

云函数偶尔超时（timeout），封装自动重试：

```javascript
function callFunction(action, data, opts) {
  opts = opts || {};
  var maxRetries = opts.maxRetries || 0;
  var attempt = 0;

  function tryCall() {
    return new Promise(function (resolve, reject) {
      wx.cloud.callFunction({ name: 'api', data: { action, data: data || {} } })
        .then(function (res) {
          if (res.result && res.result.error) { reject(new Error(res.result.error)); return; }
          resolve(res.result || {});
        }).catch(function (err) {
          var isTimeout = String(err.errMsg || '').indexOf('timeout') !== -1;
          if (isTimeout && attempt < maxRetries) {
            attempt++;
            tryCall().then(resolve).catch(reject);
            return;
          }
          reject(new Error(diagnoseError(err)));
        });
    });
  }
  return tryCall();
}
```

## AI 文字渲染（WXS 解析器）

微信小程序中 `rich-text` 组件支持有限，AI 返回的 markdown（emoji 标题 + `**粗体**`）直接当纯文本展示会很单调。以下是将纯文本 AI 反馈渲染为美观分区卡片的完整方案。

### 核心思路

1. 创建 WXS 模块解析 AI 文本 → 结构化数据 `{sections: [{icon, title, lines: [{parts: [{text, bold}]}]}]}`
2. WXML 中用 `<wxs>` 引用模块，`<block wx:for>` 遍历 sections 渲染卡片
3. 每个 section 有独立的 icon + title 头部，content 用圆点列表 + 粗体高亮

### WXS 解析器

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

### WXML 模板

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

### WXSS 样式

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

### 适用场景

- AI 周报/分析结果展示（如血压分析报告）
- AI 对话回复渲染
- 任何后端返回 emoji + markdown 格式文本需要美化展示的场景

### 注意事项

- WXS 文件必须用 `<wxs src="..." module="md" />` 在页面顶部引用，不能在 component 的 json 中声明
- WXS 的 regex 支持不如 JS 完整，emoji 匹配需要显式列出 Unicode 范围
- 如果 AI 返回格式变化（如改用 `### 标题`），需相应调整 headerMatch 正则

## 审核提交前检查清单

- [ ] 所有页面能正常加载（无白屏）
- [ ] 登录流程正常（云函数能获取 OPENID）
- [ ] 核心功能可用（记录、查看、删除）
- [ ] 无 console.error 输出
- [ ] app.json 无重复 key
- [ ] 所有 require() 的文件存在且非空
- [ ] CSS 变量全部在 app.wxss 中定义
- [ ] 云函数已部署到正确的环境
- [ ] 云环境 ID 与微信云开发控制台一致
- [ ] tabBar 页面的跳转全部用 switchTab（不用 navigateTo）
- [ ] 下拉刷新页面同时配置了 JSON 和 JS
- [ ] 表单输入有防抖处理
