@echo off
chcp 65001 >nul 2>&1
echo.
echo   ╔══════════════════════════════════════════╗
echo   ║  全局规范 · 通用多 Agent 一键部署         ║
echo   ╚══════════════════════════════════════════╝
echo.

set "SCRIPT_DIR=%~dp0"
set DEPLOYED=0

:: Claude Code
echo   ━━ Claude Code ━━
where claude >nul 2>&1
if %errorlevel%==0 (
    if not exist "%USERPROFILE%\.claude\rules" mkdir "%USERPROFILE%\.claude\rules"
    if not exist "%USERPROFILE%\.claude\skills" mkdir "%USERPROFILE%\.claude\skills"
    copy /Y "%SCRIPT_DIR%agents\claude-code\CLAUDE.md" "%USERPROFILE%\.claude\CLAUDE.md" >nul
    echo   ✓ CLAUDE.md
    for %%f in ("%SCRIPT_DIR%rules\*.md") do (
        copy /Y "%%f" "%USERPROFILE%\.claude\rules\%%~nxf" >nul
        echo   ✓ rules\%%~nxf
    )
    set /a DEPLOYED+=1
) else (
    echo   ⊘ Claude Code 未安装，跳过
)
echo.

:: Hermes Agent
echo   ━━ Hermes Agent ━━
if exist "%USERPROFILE%\.hermes" (
    if not exist "%USERPROFILE%\.hermes\skills" mkdir "%USERPROFILE%\.hermes\skills"
    copy /Y "%SCRIPT_DIR%agents\hermes\SOUL.md" "%USERPROFILE%\.hermes\SOUL.md" >nul
    echo   ✓ SOUL.md
    set /a DEPLOYED+=1
) else (
    echo   ⊘ Hermes Agent 未安装，跳过
)
echo.

:: Codex
echo   ━━ OpenAI Codex ━━
if exist "%USERPROFILE%\.codex" (
    copy /Y "%SCRIPT_DIR%agents\codex\AGENTS.md" "%USERPROFILE%\.codex\AGENTS.md" >nul
    echo   ✓ AGENTS.md
    set /a DEPLOYED+=1
) else (
    echo   ⊘ Codex 未安装，跳过
)
echo.

:: Cursor
echo   ━━ Cursor ━━
if exist "%APPDATA%\Cursor" (
    echo   提示: 将 agents\cursor\.cursorrules 复制到项目根目录
) else (
    echo   ⊘ Cursor 未安装，跳过
)
echo.

echo   ═══════════════════════════════════════
echo   部署完成！
echo   ═══════════════════════════════════════
echo.
pause
