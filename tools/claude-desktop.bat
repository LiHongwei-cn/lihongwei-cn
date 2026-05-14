@echo off
chcp 65001 >nul
title Claude Code - AI 编程助手

:: ============================================
:: Claude Code 桌面启动器
:: 保存于 GitHub 仓库 tools/claude-desktop.bat
:: 双击此文件启动 Claude Code，自动进入工作目录
:: ============================================

:: 工作目录（默认为此脚本所在目录的上一级）
set WORK_DIR=%~dp0..

:: 代理设置（如需代理请取消注释并修改端口）
:: set HTTPS_PROXY=http://127.0.0.1:7897

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

cd /d "%WORK_DIR%"

:: 启动 Claude Code（跳过权限确认）
claude --dangerously-skip-permissions

:: 如果 Claude Code 退出，暂停显示
echo.
echo  Claude Code 已退出。按任意键关闭此窗口...
pause >nul
