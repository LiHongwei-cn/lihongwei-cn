#!/usr/bin/env python3
"""GitHub Trending 爬虫 — 抓取中英文区热门仓库，生成静态报告页面"""

from datetime import datetime, timezone, timedelta
import html
import json
import os
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "index.html"

BEIJING_TZ = timezone(timedelta(hours=8))

TRENDING_EN_URL = "https://github.com/trending?since=daily"
TRENDING_ZH_URL = "https://github.com/trending?spoken_language_code=zh&since=daily"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ── scraping ──────────────────────────────────────────────────────

def fetch_trending(url, label=""):
    """抓取一个 GitHub Trending 页面，返回仓库 dict 列表"""
    print(f"  [{label}] GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    repos = []
    for article in soup.find_all("article", class_="Box-row"):
        repo = _parse_article(article)
        if repo:
            repos.append(repo)
    return repos


def _parse_article(article):
    """从单个 Box-row article 中提取仓库信息"""
    h2 = article.find("h2")
    if not h2:
        return None
    a_tag = h2.find("a")
    if not a_tag:
        return None

    href = a_tag.get("href", "").strip().lstrip("/")
    # href 格式: "owner/repo"  但有时 href 里只有 "/owner/repo"
    parts = [p for p in href.split("/") if p]
    if len(parts) < 2:
        return None
    owner, name = parts[0], parts[1]
    full_name = f"{owner}/{name}"

    # 描述
    desc_p = article.find("p")
    description = desc_p.get_text(" ", strip=True) if desc_p else ""

    # 去掉描述中多余空白
    description = re.sub(r"\s+", " ", description).strip()

    # 语言
    lang_el = article.find(attrs={"itemprop": "programmingLanguage"})
    language = lang_el.get_text(strip=True) if lang_el else ""

    # star / fork / today — 都在 stats div 里
    stats_text = article.get_text(" ", strip=True)

    total_stars = ""
    forks = ""
    stars_today = ""

    # 匹配 "123,456" 数字格式
    stars_match = re.search(r"([\d,]+)\s*stars\s*today", stats_text)
    if stars_match:
        stars_today = stars_match.group(1)

    # 从所有链接中找 star/fork
    star_a = article.find("a", href=re.compile(r"/stargazers"))
    if star_a:
        total_stars = star_a.get_text(strip=True)

    fork_a = article.find("a", href=re.compile(r"/forks"))
    if fork_a:
        forks = fork_a.get_text(strip=True)

    return {
        "full_name": full_name,
        "owner": owner,
        "name": name,
        "description": description,
        "description_cn": description,
        "url": f"https://github.com/{full_name}",
        "language": language,
        "stars": total_stars,
        "stars_today": stars_today,
        "forks": forks,
    }


# ── translation ───────────────────────────────────────────────────

def has_chinese(text):
    return any("一" <= ch <= "鿿" for ch in text)


def translate_batch(descriptions):
    """批量翻译英文描述为中文，返回翻译后的列表"""
    if not descriptions or not DEEPSEEK_API_KEY:
        return descriptions

    # 过滤掉已经是中文的和空的
    to_translate = []
    indices = []
    for i, desc in enumerate(descriptions):
        if desc and not has_chinese(desc):
            to_translate.append(desc)
            indices.append(i)

    if not to_translate:
        return descriptions

    print(f"    翻译 {len(to_translate)} 条描述...")

    # 构建批量翻译 prompt
    items = "\n".join(f"{i+1}. {d}" for i, d in enumerate(to_translate))
    prompt = (
        "将以下 GitHub 仓库的英文描述翻译成简洁的中文，保持技术术语准确。\n"
        "每条翻译一行，按序号对应，不要额外解释：\n\n" + items
    )

    try:
        client_instance = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=60.0,
        )
        resp = client_instance.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {
                    "role": "system",
                    "content": "你是技术翻译助手。将英文GitHub仓库描述翻译成简洁中文，保持技术术语。只返回翻译结果，每行一条。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        translated_text = resp.choices[0].message.content.strip()
        translated_lines = [
            re.sub(r"^\d+\.\s*", "", line).strip()
            for line in translated_text.split("\n")
            if line.strip()
        ]

        # 按索引回填
        for idx, tl in zip(indices, translated_lines):
            if idx < len(descriptions):
                descriptions[idx] = tl
            else:
                break  # 行数不匹配，保守处理
    except (ValueError, IndexError, KeyError) as e:
        print(f"    ⚠ 翻译失败: {e}")

    return descriptions


# ── HTML 生成 ─────────────────────────────────────────────────────

def _escape(text):
    return html.escape(text or "", quote=False)


def _build_repo_card(repo, accent_color):
    """生成单个仓库卡片的 HTML"""
    full_name = _escape(repo["full_name"])
    owner = _escape(repo["owner"])
    name = _escape(repo["name"])
    desc = _escape(repo["description_cn"] or repo["description"] or "（暂无描述）")
    url = _escape(repo["url"])
    lang = _escape(repo["language"])
    stars = _escape(repo["stars"])
    stars_today = _escape(repo["stars_today"])
    forks = _escape(repo["forks"])

    lang_badge = ""
    if lang:
        lang_badge = f'<span class="lang-badge">{lang}</span>'

    star_html = ""
    if stars:
        star_html += f'<span class="stat">⭐ {stars}</span>'
    if stars_today:
        star_html += f'<span class="stat today">📈 {stars_today} today</span>'
    if forks:
        star_html += f'<span class="stat">🍴 {forks}</span>'

    return f"""
    <a class="repo-card" href="{url}" target="_blank" rel="noopener">
      <div class="repo-header">
        <span class="repo-owner">{owner} /</span>
        <span class="repo-name">{name}</span>
      </div>
      <p class="repo-desc">{desc}</p>
      <div class="repo-meta">
        {lang_badge}
        {star_html}
      </div>
    </a>"""


def generate_html(zh_repos, en_repos, gen_time_str):
    """生成完整的 index.html"""
    date_str = gen_time_str[:10]
    time_str = gen_time_str[11:16] if len(gen_time_str) >= 16 else gen_time_str

    zh_cards = "\n".join(
        _build_repo_card(r, "#fb923c") for r in zh_repos
    )
    en_cards = "\n".join(
        _build_repo_card(r, "#6c8cff") for r in en_repos
    )

    zh_count = len(zh_repos)
    en_count = len(en_repos)

    zh_empty = (
        '<div class="empty-msg">暂无数据，请稍后重新生成</div>'
        if zh_count == 0
        else ""
    )
    en_empty = (
        '<div class="empty-msg">暂无数据，请稍后重新生成</div>'
        if en_count == 0
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="GitHub 每日热门仓库报告 · 中文区 & 英文区 · 自动更新">
<title>GitHub 每日热点 · LiHongwei</title>
<style>
:root {{
  --bg1: #0f0c29;
  --bg2: #302b63;
  --bg3: #24243e;
  --card: rgba(255,255,255,0.05);
  --card-hover: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.08);
  --text: #e8e8e8;
  --dim: rgba(255,255,255,0.45);
  --accent: #6c8cff;
  --orange: #fb923c;
  --red: #f87171;
  --green: #4ade80;
  --purple: #a78bfa;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(135deg, var(--bg1), var(--bg2), var(--bg3));
  color: var(--text);
  line-height: 1.7;
  min-height: 100vh;
}}
.container {{ max-width: 900px; margin: 0 auto; padding: 32px 24px 80px; }}

/* 返回链接 */
.back-link {{
  display: inline-flex; align-items: center; gap: 6px;
  color: var(--dim); font-size: 14px; text-decoration: none;
  margin-bottom: 24px; transition: color .2s;
}}
.back-link:hover {{ color: var(--accent); }}

/* Hero */
.hero {{ text-align: center; margin-bottom: 48px; }}
.hero-badge {{
  display: inline-block; padding: 4px 16px;
  border-radius: 20px; font-size: 13px; color: var(--accent);
  background: rgba(108,140,255,0.1); border: 1px solid rgba(108,140,255,0.2);
  margin-bottom: 16px;
}}
.hero h1 {{
  font-size: 40px; font-weight: 800; letter-spacing: -0.5px;
  background: linear-gradient(135deg, #a78bfa, #6c8cff, #4ade80);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 8px;
}}
.hero .subtitle {{ color: var(--dim); font-size: 16px; }}
.hero .update-time {{ color: rgba(255,255,255,0.25); font-size: 13px; margin-top: 6px; }}

/* 导航标签 */
.nav-tabs {{
  display: flex; gap: 10px; justify-content: center; margin-bottom: 40px;
  flex-wrap: wrap;
}}
.nav-tab {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 24px; border-radius: 12px;
  font-size: 15px; font-weight: 600; text-decoration: none;
  border: 1px solid var(--border); color: var(--text);
  background: var(--card); transition: all .2s;
}}
.nav-tab:hover {{ background: var(--card-hover); border-color: rgba(255,255,255,0.15); }}
.nav-tab.zh {{ border-color: rgba(251,146,60,0.3); }}
.nav-tab.zh:hover {{ background: rgba(251,146,60,0.1); }}
.nav-tab.en {{ border-color: rgba(108,140,255,0.3); }}
.nav-tab.en:hover {{ background: rgba(108,140,255,0.1); }}
.nav-tab .count {{ font-size: 12px; color: var(--dim); font-weight: 400; }}

/* 区块标题 */
.section-header {{
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
  padding-bottom: 12px; border-bottom: 1px solid var(--border);
}}
.section-header .icon {{ font-size: 24px; }}
.section-header h2 {{ font-size: 22px; font-weight: 700; }}
.section-header .count {{ font-size: 14px; color: var(--dim); }}
.section-divider {{ height: 40px; }}

/* 仓库卡片网格 */
.repo-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 12px; margin-bottom: 16px;
}}
.repo-card {{
  display: flex; flex-direction: column; gap: 8px;
  padding: 20px 24px; border-radius: 14px;
  background: var(--card); border: 1px solid var(--border);
  text-decoration: none; color: var(--text);
  transition: all .2s;
}}
.repo-card:hover {{
  background: var(--card-hover); border-color: rgba(255,255,255,0.15);
  transform: translateY(-1px);
}}
.repo-header {{ font-size: 16px; }}
.repo-owner {{ color: var(--dim); font-weight: 400; }}
.repo-name {{ color: var(--accent); font-weight: 700; }}
.repo-desc {{
  font-size: 14px; color: var(--dim); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}}
.repo-meta {{
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  margin-top: 4px;
}}
.lang-badge {{
  font-size: 12px; padding: 2px 10px; border-radius: 10px;
  background: rgba(255,255,255,0.06); color: var(--accent);
}}
.stat {{ font-size: 12px; color: rgba(255,255,255,0.35); }}
.stat.today {{ color: var(--orange); }}

.empty-msg {{
  text-align: center; padding: 48px 24px; color: var(--dim);
  font-size: 15px;
}}

/* Footer */
.footer {{
  text-align: center; padding: 32px 0 0; font-size: 12px;
  color: rgba(255,255,255,0.2); border-top: 1px solid rgba(255,255,255,0.04);
  margin-top: 48px;
}}
.footer a {{ color: rgba(255,255,255,0.3); text-decoration: none; }}
.footer a:hover {{ color: var(--accent); }}

/* 响应式 */
@media (max-width: 640px) {{
  .container {{ padding: 20px 16px 60px; }}
  .hero h1 {{ font-size: 28px; }}
  .repo-grid {{ grid-template-columns: 1fr; }}
  .nav-tab {{ padding: 8px 16px; font-size: 14px; }}
}}
</style>
</head>
<body>

<div class="container">

  <a class="back-link" href="../">← 返回主页</a>

  <div class="hero">
    <div class="hero-badge">每日更新 · 自动爬取</div>
    <h1>GitHub 每日热点</h1>
    <p class="subtitle">中文区 &amp; 英文区热门开源仓库一览</p>
    <p class="update-time">🕐 更新时间：{date_str} {time_str}（北京时间）</p>
  </div>

  <div class="nav-tabs">
    <a class="nav-tab zh" href="#zh-section">
      🔥 中文区热门 <span class="count">({zh_count})</span>
    </a>
    <a class="nav-tab en" href="#en-section">
      🌍 英文区热门 <span class="count">({en_count})</span>
    </a>
  </div>

  <!-- 中文区 -->
  <div id="zh-section">
    <div class="section-header">
      <span class="icon">🔥</span>
      <h2>中文区热门</h2>
      <span class="count">共 {zh_count} 个仓库</span>
    </div>
    {zh_empty}
    <div class="repo-grid">
      {zh_cards}
    </div>
  </div>

  <div class="section-divider"></div>

  <!-- 英文区（已翻译） -->
  <div id="en-section">
    <div class="section-header">
      <span class="icon">🌍</span>
      <h2>英文区热门</h2>
      <span class="count">共 {en_count} 个仓库（描述已翻译为中文）</span>
    </div>
    {en_empty}
    <div class="repo-grid">
      {en_cards}
    </div>
  </div>

  <div class="page-counter" style="text-align:center;padding:24px 0 8px;font-size:13px;color:rgba(255,255,255,0.2)">
    本页被阅读 <span id="page-count">...</span> 次
  </div>

  <div class="footer">
    <a href="https://github.com/LiHongwei-cn/lihongwei-cn" target="_blank">GitHub</a>
    &nbsp;·&nbsp; 数据来源：GitHub Trending
    &nbsp;·&nbsp; LiHongwei
  </div>

</div>

<script>
(async function(){{
  try {{
    let r = await fetch('https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/stats.json');
    let s = await r.json();
    document.getElementById('page-count').textContent = s['github-trending'] || '...';
  }} catch(e) {{
    document.getElementById('page-count').textContent = '...';
  }}
}})();
</script>
<img src="https://api.counterapi.dev/v1/lihongwei-cn/github-trending/up" style="display:none" alt="" />
</body>
</html>"""


# ── stats sync ────────────────────────────────────────────────────

def sync_stats_json():
    """从 counterapi.dev 拉取所有页面访问量，同步到 stats.json"""
    stats_file = BASE_DIR.parent / "stats.json"

    PAGES = [
        "home", "matlab-tool", "desktop-launcher", "claude-code-tutorial",
        "vpn-guide", "win-optimize", "github-trending", "ccs-launcher", "global-specs",
    ]

    try:
        stats = {}
        if stats_file.exists():
            stats = json.loads(stats_file.read_text(encoding="utf-8"))

        for page in PAGES:
            try:
                resp = requests.get(
                    f"https://api.counterapi.dev/v1/lihongwei-cn/{page}/",
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    stats[page] = data.get("count", 0)
            except Exception:
                continue

        stats_file.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
        print(f"    stats.json 已同步: {len(PAGES)} 个页面")
    except Exception as e:
        print(f"    ⚠ stats.json 同步失败: {e}")


# ── main ──────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  GitHub Trending 爬虫")
    print("=" * 50)

    # 1. 抓取
    print("\n📡 抓取数据...")
    zh_repos = []
    en_repos = []

    try:
        zh_repos = fetch_trending(TRENDING_ZH_URL, "中文区")
        print(f"    中文区：{len(zh_repos)} 个仓库")
    except Exception as e:
        print(f"    ⚠ 中文区抓取失败: {e}")

    try:
        en_repos = fetch_trending(TRENDING_EN_URL, "英文区")
        print(f"    英文区：{len(en_repos)} 个仓库")
    except Exception as e:
        print(f"    ⚠ 英文区抓取失败: {e}")

    if not zh_repos and not en_repos:
        print("\n❌ 两个区域均无数据，退出。")
        sys.exit(1)

    # 2. 翻译英文区描述
    if en_repos and DEEPSEEK_API_KEY:
        print("\n🌐 翻译英文区描述...")
        descs = [r["description"] for r in en_repos]
        translated = translate_batch(descs)
        for repo, desc_cn in zip(en_repos, translated):
            repo["description_cn"] = desc_cn
        print("    ✓ 翻译完成")
    elif en_repos:
        print("\n⚠ 未设置 DEEPSEEK_API_KEY，英文描述保持原文")

    # 3. 生成 HTML
    gen_time = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    print(f"\n📄 生成报告页面...")
    html_content = generate_html(zh_repos, en_repos, gen_time)

    OUTPUT_FILE.write_text(html_content, encoding="utf-8")
    print(f"✅ 报告已保存: {OUTPUT_FILE}")
    print(f"    中文区 {len(zh_repos)} 个 · 英文区 {len(en_repos)} 个")

    # 4. 同步首页访问量到 stats.json
    print("\n📊 同步访问统计...")
    sync_stats_json()


if __name__ == "__main__":
    main()
