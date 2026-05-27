# WeChat Mini Program Optimization Patterns

## Common Optimizations

### 1. Add tabBar Bottom Navigation
Instead of `navigateTo` for tab switching, use `wx.switchTab` with tabBar config in app.json:

```json
{
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#2c7a4f",
    "backgroundColor": "#ffffff",
    "list": [
      { "pagePath": "pages/index/index", "text": "首页", "iconPath": "assets/tab-home.png", "selectedIconPath": "assets/tab-home-active.png" },
      ...
    ]
  }
}
```

Icons must be PNG files (81x81 recommended). Generate with Python if needed.

### 2. Enable Pull-Down Refresh
In page JSON:
```json
{
  "enablePullDownRefresh": true,
  "backgroundTextStyle": "dark"
}
```

In page JS:
```javascript
onPullDownRefresh() {
  this.loadData().finally(() => wx.stopPullDownRefresh());
}
```

### 3. Input Debouncing
Don't validate on every keystroke. Use debounce:

```javascript
let validateTimer = null;

onSystolicInput(e) {
  this.setData({ systolic: e.detail.value });
  this.debounceValidate('systolic');
},

debounceValidate(field) {
  if (validateTimer) clearTimeout(validateTimer);
  validateTimer = setTimeout(() => {
    if (field === 'systolic') this.validateSys();
  }, 300);
}
```

### 4. Pre-Login on App Launch
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

### 5. Tab Navigation Fix
After adding tabBar, change all `navigateTo` to `switchTab` for tab pages:
```javascript
// Before
goRecord() { wx.navigateTo({ url: '/pages/record/record' }); }
// After
goRecord() { wx.switchTab({ url: '/pages/record/record' }); }
```

## Pitfalls

- tabBar icons MUST be local PNG files (no URLs, no SVG)
- switchTab cannot pass query parameters
- Every tab page needs its own JSON config with usingComponents
- Pull-down refresh requires both page JSON config AND onPullDownRefresh handler
