# HTML 中英双语切换实现模式

## 问题

同一个 HTML 元素写两个 `class` 属性时浏览器只认第一个，第二个被静默忽略：
```html
<!-- 错误：class="show" 被忽略 -->
<div class="hero-quote" data-lang="zh" class="show">中文</div>
```

## 正确方案：body 类名切换

CSS 默认显示中文，隐藏英文。点击英文按钮时给 body 加 `lang-en` 类：

```css
[data-lang="en"] { display: none; }
body.lang-en [data-lang="en"] { display: revert; }
body.lang-en [data-lang="zh"] { display: none; }
```

JS 只需切换 body 类名：
```javascript
function switchLang(lang, btn) {
  document.querySelectorAll('.lang-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  if (lang === 'en') {
    document.body.classList.add('lang-en');
  } else {
    document.body.classList.remove('lang-en');
  }
}
```

HTML 中每个区块写两份，用 `data-lang` 区分：
```html
<div data-lang="zh">中文内容</div>
<div data-lang="en">English content</div>
```

## 优势

- 不需要遍历 DOM 操作每个元素
- CSS 控制显隐，性能更好
- 不会出现 `class` 属性重复的 bug
- `display: revert` 让 span 保持 inline、div 保持 block
