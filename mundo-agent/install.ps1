# MUNDO Agent — Windows 一键安装脚本
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "    ╔══════════════════════════════════════════╗"
Write-Host "    ║         👑 MUNDO Agent 安装程序          ║"
Write-Host "    ╚══════════════════════════════════════════╝"
Write-Host ""

# 检查 Python
try { $pyVer = python --version 2>&1 } catch { $pyVer = "" }
if (-not $pyVer -or $pyVer -notmatch "3\.(\d+)") {
    Write-Host "✗ 未找到 Python。请安装："
    Write-Host "  winget install Python.Python.3.12"
    Write-Host "  或: https://www.python.org/downloads/"
    exit 1
}
$minor = [int]$matches[1]
if ($minor -lt 10) {
    Write-Host "✗ Python 版本太低（需要 3.10+）"
    exit 1
}
Write-Host "✓ $pyVer"

# 检查 Git
try { $gitVer = git --version 2>&1 } catch { $gitVer = "" }
if (-not $gitVer) {
    Write-Host "✗ 未找到 Git。请安装："
    Write-Host "  winget install Git.Git"
    Write-Host "  或: https://git-scm.com/download/win"
    exit 1
}
Write-Host "✓ $gitVer"

# 安装目录
$mundoDir = "$env:USERPROFILE\.hermes\mundo-agent"
New-Item -ItemType Directory -Force -Path $mundoDir | Out-Null

# 下载文件
$repoUrl = "https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent"
Write-Host ""
Write-Host "下载蒙多 Agent 文件..."

$files = @("mundo.py", "engine.py", "llm.py", "tools.py", "agents.py", "delegation.py", "approval.py", "cloud_sync.py", "setup.py", "mundo.bat")
foreach ($f in $files) {
    try {
        Invoke-WebRequest -Uri "$repoUrl/$f" -OutFile "$mundoDir\$f" -UseBasicParsing
        Write-Host "  ✓ $f"
    } catch {
        Write-Host "  ✗ $f (下载失败)"
    }
}

# 添加到 PATH
$binDir = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
@"
@echo off
python "%USERPROFILE%\.hermes\mundo-agent\mundo.py" %*
"@ | Out-File -FilePath "$binDir\mundo.bat" -Encoding ascii

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binDir", "User")
    $env:Path += ";$binDir"
    Write-Host "✓ 已添加到 PATH"
}

# 从云仓库拉取 Skills 和全局规范
Write-Host ""
Write-Host "从云仓库拉取 Skills 和全局规范..."
$repoTmp = "$env:TEMP\mundo-repo-$PID"
try {
    git clone --depth=1 https://github.com/LiHongwei-cn/lihongwei-cn.git $repoTmp 2>$null

    $cloudSkills = "$repoTmp\global-specs\skills"
    if (Test-Path $cloudSkills) {
        $skillsDir = "$env:USERPROFILE\.hermes\skills"
        New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
        $cpCount = 0
        Get-ChildItem $cloudSkills -Directory | ForEach-Object {
            $skillMd = Join-Path $_.FullName "SKILL.md"
            if (Test-Path $skillMd) {
                $dst = Join-Path $skillsDir $_.Name
                New-Item -ItemType Directory -Force -Path $dst | Out-Null
                Copy-Item $skillMd (Join-Path $dst "SKILL.md") -Force
                $cpCount++
            }
        }
        Write-Host "  ✓ 已部署 $cpCount 个 Skills"
    }

    $cloudSpecs = "$repoTmp\global-specs\rules"
    if (Test-Path $cloudSpecs) {
        $rulesDir = "$env:USERPROFILE\.hermes\rules"
        New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
        Copy-Item "$cloudSpecs\*.md" $rulesDir -Force 2>$null
        Write-Host "  ✓ 已部署全局规范"
    }
} catch {
    Write-Host "  ⚠ 云端拉取失败（可稍后手动同步）"
} finally {
    Remove-Item -Recurse -Force $repoTmp -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║         👑 安装完成！                    ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""
Write-Host "已部署内容："
Write-Host "  • MUNDO Agent 引擎（9 个 Python 模块）"
Write-Host "  • Skills（从云仓库自动拉取）"
Write-Host "  • 全局规范（从云仓库自动拉取）"
Write-Host ""
Write-Host "启动蒙多（重启终端后）："
Write-Host "  mundo              # 交互模式"
Write-Host "  mundo -q '问题'    # 单次查询"
Write-Host ""
Write-Host "首次启动会引导你选择 AI 模型并输入 API Key。"
Write-Host "Key 仅保存在本地，不会上传。"
Write-Host ""
