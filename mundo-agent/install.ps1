# MUNDO Agent — Windows 一键安装脚本
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  MUNDO Agent 安装程序"
Write-Host ""

# 检查 Python
$PYTHON_CMD = $null
foreach ($cmd in @("python3.12", "python3.11", "python3.10", "python3", "python")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
        $parts = $ver.Split(".")
        if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) {
            $PYTHON_CMD = $cmd
            break
        }
    } catch {}
}

if (-not $PYTHON_CMD) {
    Write-Host "错误: 需要 Python 3.10+"
    Write-Host "  winget install Python.Python.3.12"
    Write-Host "  或: https://www.python.org/downloads/"
    exit 1
}
Write-Host "使用 $PYTHON_CMD"

# 安装目录
$mundoDir = "$env:USERPROFILE\.hermes\mundo-agent"
New-Item -ItemType Directory -Force -Path $mundoDir | Out-Null

# 创建虚拟环境
if (-not (Test-Path "$mundoDir\venv")) {
    Write-Host "创建虚拟环境..."
    & $PYTHON_CMD -m venv "$mundoDir\venv"
}

# 安装依赖
Write-Host "安装依赖..."
& "$mundoDir\venv\Scripts\pip.exe" install --quiet requests beautifulsoup4 prompt_toolkit rich
Write-Host "依赖就绪"

# 检查 Git
try { $gitVer = git --version 2>&1 } catch { $gitVer = "" }
if (-not $gitVer) {
    Write-Host "警告: 未找到 Git，部分功能受限"
    Write-Host "  winget install Git.Git"
} else {
    Write-Host "Git: $gitVer"
}

# 添加到 PATH
$binDir = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
@"
@echo off
call "%USERPROFILE%\.hermes\mundo-agent\venv\Scripts\activate.bat"
python "%USERPROFILE%\.hermes\mundo-agent\mundo.py" %*
"@ | Out-File -FilePath "$binDir\mundo.bat" -Encoding ascii

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binDir", "User")
    $env:Path += ";$binDir"
    Write-Host "已添加到 PATH"
}

Write-Host ""
Write-Host "安装完成！"
Write-Host ""
Write-Host "启动蒙多（重启终端后）："
Write-Host "  mundo              # 交互模式"
Write-Host "  mundo -q '问题'    # 单次查询"
Write-Host ""
Write-Host "首次启动会引导你选择 AI 模型并输入 API Key。"
Write-Host "Key 仅保存在本地，不会上传。"
Write-Host ""
