#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Docker Desktop 一键安装脚本 (Windows)
.DESCRIPTION
    自动检测并安装 Docker Desktop，解决国内网络慢的问题。
    使用方法: 右键此文件 -> "使用 PowerShell 运行"
    或者: 在 PowerShell 中运行 .\docker_install.ps1
#>

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Docker Desktop 一键安装脚本" -ForegroundColor Cyan
Write-Host "   (Windows 10/11)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装 Docker
$dockerInstalled = $false
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker 已安装: $dockerVersion" -ForegroundColor Green
        Write-Host "[提示] 你不需要重新安装，可以直接跳到构建镜像步骤。" -ForegroundColor Yellow
        $dockerInstalled = $true
    }
} catch {
    # 未安装，继续
}

if ($dockerInstalled) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   后续操作" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 确保 Docker Desktop 正在运行（任务栏右下角找鲸鱼图标）"
    Write-Host "2. 在项目目录执行: docker compose build"
    Write-Host "3. 构建完成后执行: docker compose run --rm bili-video --task basic_test"
    Write-Host ""
    pause
    exit 0
}

Write-Host "[信息] Docker 未安装，开始自动安装..." -ForegroundColor Yellow
Write-Host ""

# 检查 winget 是否可用
$wingetAvailable = $false
try {
    $wingetVersion = winget --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] winget 可用 (版本: $wingetVersion)" -ForegroundColor Green
        $wingetAvailable = $true
    }
} catch {
    Write-Host "[警告] winget 不可用，将使用备用方案" -ForegroundColor Yellow
}

if ($wingetAvailable) {
    Write-Host ""
    Write-Host "[安装] 正在通过 winget 安装 Docker Desktop..." -ForegroundColor Cyan
    Write-Host "       这可能需要 3-10 分钟，取决于网速。" -ForegroundColor Yellow
    Write-Host ""

    winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] Docker Desktop 安装成功！" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[失败] winget 安装失败，请尝试手动安装。" -ForegroundColor Red
        Write-Host "       手动下载地址: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        pause
        exit 1
    }
} else {
    # 备用方案：直接从 Docker 官网下载
    Write-Host ""
    Write-Host "[信息] 正在使用备用方案：从 Docker 官网下载..." -ForegroundColor Yellow
    Write-Host ""

    $dockerInstallerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $tempDir = [System.IO.Path]::GetTempPath()
    $installerPath = Join-Path $tempDir "DockerDesktopInstaller.exe"

    Write-Host "[下载] 正在下载 Docker Desktop 安装包 (约 600MB)..." -ForegroundColor Cyan
    Write-Host "       如果下载很慢，建议挂 VPN 或使用上面 winget 的方式。" -ForegroundColor Yellow

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $dockerInstallerUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "[OK] 下载完成" -ForegroundColor Green
    } catch {
        Write-Host "[失败] 下载失败: $_" -ForegroundColor Red
        Write-Host "       请手动下载: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        pause
        exit 1
    }

    Write-Host "[安装] 正在运行安装程序..." -ForegroundColor Cyan
    Write-Host "       安装向导出现后，一路点 'OK' 就行，不用改任何设置。" -ForegroundColor Yellow

    Start-Process -FilePath $installerPath -ArgumentList "install", "--quiet", "--accept-license" -Wait

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker Desktop 安装完成" -ForegroundColor Green
    } else {
        Write-Host "[警告] 静默安装可能失败，安装向导应已弹出，请手动完成。" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   重要！安装后的步骤" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 【必须】重启电脑" -ForegroundColor Yellow
Write-Host "   装完 Docker Desktop 后需要重启，否则会报错。"
Write-Host ""
Write-Host "2. 【必须】首次启动 Docker Desktop" -ForegroundColor Yellow
Write-Host "   重启后在开始菜单搜索 'Docker Desktop'，点击启动。"
Write-Host "   首次启动需要同意服务协议（点 Accept 就行）。"
Write-Host "   看到任务栏右下角出现鲸鱼图标即启动成功。"
Write-Host ""
Write-Host "3. 【如果启动报错 WSL2】" -ForegroundColor Yellow
Write-Host "   以管理员身份打开 PowerShell，执行:"
Write-Host "   wsl --install"
Write-Host "   然后重启电脑，再打开 Docker Desktop。"
Write-Host ""
Write-Host "4. Docker 启动成功后，在项目文件夹打开 PowerShell，执行:" -ForegroundColor Yellow
Write-Host "   docker compose build"
Write-Host "   docker compose run --rm bili-video --task basic_test"
Write-Host ""

pause
