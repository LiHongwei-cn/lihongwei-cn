@echo off
chcp 65001 >nul
echo ========================================
echo AI 热点每日抓取 + 蒙多学习
echo ========================================

cd /d "%~dp0.."

echo [1/3] 抓取今日热点...
python tools/ai-hotspot-crawler.py
if errorlevel 1 (
    echo 抓取失败！
    pause
    exit /b 1
)

echo [2/3] 蒙多分析学习...
python tools/ai-hotspot-analyzer.py

echo [3/3] 同步到 GitHub...
git add docs/ai-hotspots/ tools/ai-hotspot-*.py
git commit -m "docs: AI 热点日报 %date%"
git push

echo ========================================
echo 完成！热点已保存并同步
echo ========================================
pause
