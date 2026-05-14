@echo off
chcp 65001 >nul
title Claude Code - AI 编程助手

:: 工作目录（此脚本所在目录的上一级，即项目根目录）
set WORK_DIR=%~dp0..

:: 强制 CLI 模式，防止自动打开 VS Code
set CLAUDE_CODE_ENTRYPOINT=cli

cd /d "%WORK_DIR%"

echo.
echo  🦀 Claude Code 启动中...
echo  ═══════════════════════════════════
echo  工作目录: %WORK_DIR%
echo.
echo  💡 提示：启动后输入 /help 查看所有命令
echo      输入 exit 退出 Claude Code
echo.
echo  ⏳ 正在进入目录并启动...
echo.

:: 检测 Windows Terminal，有则用它打开（支持交互界面），否则回退 cmd
where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    wt -d "%WORK_DIR%" cmd /k "set CLAUDE_CODE_ENTRYPOINT=cli && claude --dangerously-skip-permissions --no-chrome"
    echo  ✅ 已在 Windows Terminal 中启动，请切换到新窗口。
    echo.
    timeout /t 3 >nul
    exit /b
)

:: 无 Windows Terminal 时直接启动
claude --dangerously-skip-permissions --no-chrome

echo.
echo  Claude Code 已退出。按任意键关闭此窗口...
pause >nul
