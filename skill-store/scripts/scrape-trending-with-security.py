#!/usr/bin/env python3
"""
每日爬取 GitHub Trending 中 AI Agent 相关项目，保存到 skill-store
集成 NVIDIA SkillSpector 安全检查
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from scrapling.fetchers import Fetcher

# 添加SkillSpector到路径
SKILLSPECTOR_PATH = Path.home() / 'Desktop' / 'SkillSpector'
sys.path.insert(0, str(SKILLSPECTOR_PATH))

from skill_security_integration import check_skill_before_add, generate_security_badge

# 配置
KEYWORDS = [
    'ai agent', 'ai-agent', 'agent', 'llm agent', 'autonomous agent',
    'mcp', 'model context protocol', 'rag', 'retrieval augmented',
    'langchain', 'autogen', 'crewai', 'metagpt', 'camel',
    'openai', 'anthropic', 'claude', 'gpt', 'deepseek',
    'prompt engineering', 'chain of thought', 'function calling',
    'tool use', 'multi-agent', 'agentic'
]
DATA_DIR = os.path.expanduser('~/Desktop/lihongwei-cn/skill-store/data')
TODAY = datetime.now().strftime('%Y-%m-%d')

def is_ai_related(name, desc):
    """判断项目是否与 AI Agent 相关"""
    text = f"{name} {desc}".lower()
    return any(kw in text for kw in KEYWORDS)

def scrape_trending():
    """爬取 GitHub Trending 页面"""
    url = 'https://github.com/trending'
    page = Fetcher.get(url, timeout=90)
    
    projects = []
    for article in page.css('article.Box-row'):
        name_el = article.css('h2 a')
        if not name_el:
            continue
        href = name_el[0].attrib.get('href', '')
        name = href.strip('/')
        
        desc_el = article.css('p')
        desc = desc_el[0].text.strip() if desc_el else ''
        
        lang_el = article.css('[itemprop="programmingLanguage"]')
        lang = lang_el[0].text.strip() if lang_el else ''
        
        star_links = article.css('a.Link--muted')
        stars = ''
        for link in star_links:
            href_val = link.attrib.get('href', '')
            if href_val and '/stargazers' in href_val:
                stars = link.text.strip()
                break
        
        today_stars = ''
        star_today = article.css('span.d-inline-block.float-sm-right')
        if star_today:
            today_stars = star_today[0].text.strip()
        
        if is_ai_related(name, desc):
            projects.append({
                'name': name,
                'url': f'https://github.com/{name}',
                'description': desc,
                'language': lang,
                'stars': stars,
                'today_stars': today_stars,
                'date': TODAY
            })
    
    return projects

def clone_and_check_security(project):
    """克隆项目并进行安全检查"""
    import subprocess
    
    name = project['name'].replace('/', '_')
    clone_dir = Path(DATA_DIR) / 'temp' / name
    
    # 克隆项目
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', project['url'], str(clone_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
    except Exception as e:
        print(f"  克隆失败: {e}")
        return None
    
    # 进行安全检查
    if clone_dir.exists():
        result = check_skill_before_add(clone_dir, name)
        
        # 清理临时目录
        import shutil
        shutil.rmtree(clone_dir, ignore_errors=True)
        
        return result
    
    return None

def save_projects(projects, security_results):
    """保存到 JSON 文件，包含安全检查结果"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f'{TODAY}.json')
    
    # 合并安全检查结果
    for project in projects:
        name = project['name'].replace('/', '_')
        if name in security_results:
            security = security_results[name]
            project['security'] = {
                'risk_score': security['risk_score'],
                'risk_level': security['risk_level'],
                'passed': security['passed'],
                'badge': generate_security_badge(security['risk_score'])
            }
        else:
            project['security'] = {
                'risk_score': -1,
                'risk_level': '未检查',
                'passed': False,
                'badge': {'status': 'unchecked', 'label': '未检查', 'color': '#6b7280', 'icon': '❓'}
            }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    
    return filepath

def main():
    print(f'[{TODAY}] 开始爬取 GitHub Trending...')
    projects = scrape_trending()
    print(f'[{TODAY}] 发现 {len(projects)} 个 AI Agent 相关项目')
    
    # 进行安全检查
    print(f'[{TODAY}] 开始安全检查...')
    security_results = {}
    
    for i, project in enumerate(projects, 1):
        print(f'  [{i}/{len(projects)}] 检查: {project["name"]}...', end=' ')
        result = clone_and_check_security(project)
        
        if result:
            name = project['name'].replace('/', '_')
            security_results[name] = result
            
            if result['passed']:
                print(f"✅ {result['risk_level']}")
            else:
                print(f"❌ {result['risk_level']}")
        else:
            print("⚠️ 检查失败")
    
    # 保存结果
    filepath = save_projects(projects, security_results)
    
    # 统计
    passed = sum(1 for r in security_results.values() if r['passed'])
    failed = len(security_results) - passed
    
    print(f'\n[{TODAY}] 完成:')
    print(f'  - 总项目数: {len(projects)}')
    print(f'  - 通过安全检查: {passed}')
    print(f'  - 未通过安全检查: {failed}')
    print(f'  - 保存到: {filepath}')
    
    # 返回未通过的项目列表
    if failed > 0:
        print(f'\n[{TODAY}] 未通过安全检查的项目:')
        for name, result in security_results.items():
            if not result['passed']:
                print(f'  - {name}: {result["risk_level"]} (分数: {result["risk_score"]})')
    
    return projects

if __name__ == '__main__':
    main()
