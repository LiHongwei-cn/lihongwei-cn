---
name: selenium-element-screenshot
description: "用 Selenium 对网页各区块逐个截图（元素级 screenshot），支持 Retina 高清。适用场景：用户要求截取网页内容、分区块截图、网页可视化存档。"
triggers:
  - 截图
  - screenshot
  - 网页截图
  - 区块截图
  - 页面截图
  - selenium截图
---

# Selenium 元素级截图

对网页各区块逐个截取独立 PNG 文件，支持 Retina 2x 高清。

## 依赖

```bash
pip3 install selenium
# Chrome/ChromeDriver 需已安装（brew install --cask google-chrome）
```

## 核心流程

1. 用 Selenium 打开页面（本地 `file://` 或远程 URL）
2. 用 JS 注入 ID 给目标区块（避免 CSS 选择器踩坑）
3. 逐个元素 `.screenshot()` 保存 PNG

## 坑：nth-of-type 不能和属性选择器混用

```python
# ❌ 错误 — nth-of-type 按标签类型计数，忽略 [data-lang]
driver.find_element("css selector", ".section[data-lang='zh']:nth-of-type(1)")

# ✅ 正确 — 用 JS 注入 ID，再按 ID 选择
driver.execute_script("""
    document.querySelectorAll('.section[data-lang="zh"]')
        .forEach((s, i) => s.id = 'sec-' + i);
""")
driver.find_element("css selector", "#sec-0")
```

## 高清截图配置

```python
options = Options()
options.add_argument("--window-size=1440,900")
options.add_argument("--force-device-scale-factor=2")  # Retina 2x
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
```

## 元素截图

```python
elem = driver.find_element("css selector", "#target")
elem.screenshot("/path/to/output.png")  # 只截该元素区域
```

## 完整脚本模板

```python
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

OUTPUT_DIR = os.path.expanduser("~/Desktop/screenshots")
HTML_PATH = "file:///path/to/page.html"

os.makedirs(OUTPUT_DIR, exist_ok=True)

options = Options()
options.add_argument("--window-size=1440,900")
options.add_argument("--force-device-scale-factor=2")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=options)
driver.get(HTML_PATH)

# JS 注入 ID
driver.execute_script("""
    const targets = document.querySelectorAll('.your-selector');
    targets.forEach((el, i) => el.id = 'block-' + i);
""")

BLOCKS = [
    ("#block-0", "01-section-name", "描述"),
    ("#block-1", "02-section-name", "描述"),
]

for selector, name, desc in BLOCKS:
    elem = driver.find_element("css selector", selector)
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    elem.screenshot(path)
    size_kb = os.path.getsize(path) / 1024
    print(f"  {name}.png  {size_kb:.0f}KB")

driver.quit()
```
