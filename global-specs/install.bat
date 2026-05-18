@echo off
chcp 65001 >nul
title Claude Code 全局规范 · 一键部署

echo.
echo   Claude Code 全局规范 · 一键部署
echo   =================================
echo.

set "SRC=%~dp0"
set "SRC=%SRC:~0,-1%"
set "CLAUDEDIR=%USERPROFILE%\.claude"

:: ── 1. 检查 Claude Code ──
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo   [!] claude 未安装
    echo   安装命令: npm install -g @anthropic-ai/claude-code
    echo.
)

:: ── 2. 创建目录 ──
if not exist "%CLAUDEDIR%\rules" mkdir "%CLAUDEDIR%\rules"
if not exist "%CLAUDEDIR%\skills" mkdir "%CLAUDEDIR%\skills"

:: ── 3. 部署全局指令 ──
echo   [1/5] 全局 CLAUDE.md
copy /Y "%SRC%\CLAUDE.md" "%CLAUDEDIR%\CLAUDE.md" >nul
echo     √ %CLAUDEDIR%\CLAUDE.md

:: ── 4. 部署规范 ──
echo   [2/5] 规范文件
for %%f in ("%SRC%\rules\*.md") do (
    copy /Y "%%f" "%CLAUDEDIR%\rules\" >nul
    echo     √ %CLAUDEDIR%\rules\%%~nxf
)

:: ── 5. 部署 Skills ──
echo   [3/5] Skills
for /d %%d in ("%SRC%\skills\*") do (
    if not exist "%CLAUDEDIR%\skills\%%~nd" mkdir "%CLAUDEDIR%\skills\%%~nd"
    xcopy /E /Y /Q "%%d" "%CLAUDEDIR%\skills\%%~nd\" >nul
    echo     √ %CLAUDEDIR%\skills\%%~nd\
)

:: ── 6. 部署配置文件 ──
echo   [4/5] 配置文件
if not exist "%CLAUDEDIR%\settings.json" (
    copy /Y "%SRC%\settings.json" "%CLAUDEDIR%\settings.json" >nul
    echo     √ %CLAUDEDIR%\settings.json (新建)
) else (
    echo     ! %CLAUDEDIR%\settings.json 已存在，跳过
)
if not exist "%CLAUDEDIR%\settings.local.json" (
    copy /Y "%SRC%\settings.local.json" "%CLAUDEDIR%\settings.local.json" >nul
    echo     √ %CLAUDEDIR%\settings.local.json (新建)
) else (
    echo     ! %CLAUDEDIR%\settings.local.json 已存在，跳过
)

:: ── 7. 完成 ──
echo   [5/5] 完成
echo.
echo   ═══════════════════════════════════
echo   部署完成！
echo   ═══════════════════════════════════
echo.
echo   后续步骤:
echo   1. 编辑 %%USERPROFILE%%\.claude\settings.json 填入 API Key
echo   2. 运行 claude 进入对话
echo   3. 输入 /neat 测试 skill 是否正常加载
echo.
pause
