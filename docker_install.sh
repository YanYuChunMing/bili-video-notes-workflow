#!/usr/bin/env bash
#
# Docker 一键安装脚本 (Linux / macOS)
#
# 使用方法:
#   chmod +x docker_install.sh
#   ./docker_install.sh
#

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   Docker 一键安装脚本${NC}"
echo -e "${CYAN}   (Linux / macOS)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Darwin)    echo "macos" ;;
        Linux)     echo "linux" ;;
        *)         echo "unknown" ;;
    esac
}

OS=$(detect_os)

# 检查是否已安装 Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}[OK] Docker 已安装: $DOCKER_VERSION${NC}"
    echo -e "${YELLOW}[提示] 无需重新安装。${NC}"
    echo ""
    echo -e "${CYAN}后续操作:${NC}"
    echo "  cd 到项目目录"
    echo "  docker compose build"
    echo "  docker compose run --rm bili-video --task basic_test"
    echo ""
    exit 0
fi

echo -e "${YELLOW}[信息] Docker 未安装，开始自动安装...${NC}"
echo ""

if [ "$OS" = "macos" ]; then
    # ============ macOS ============
    echo -e "${CYAN}[检测] macOS 系统${NC}"

    # 检查 Homebrew
    if command -v brew &> /dev/null; then
        echo -e "${GREEN}[OK] Homebrew 可用，通过 brew 安装 Docker Desktop${NC}"
        echo ""
        brew install --cask docker
        echo ""
        echo -e "${GREEN}[OK] Docker Desktop 安装完成${NC}"
    else
        echo -e "${YELLOW}[信息] 未安装 Homebrew，正在先安装 Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo ""
        echo -e "${YELLOW}[信息] 正在安装 Docker Desktop...${NC}"
        brew install --cask docker
        echo ""
        echo -e "${GREEN}[OK] Docker Desktop 安装完成${NC}"
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}   重要！安装后的步骤${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}1. 在"应用程序"中找到 Docker，双击启动。${NC}"
    echo -e "${YELLOW}   首次启动需要同意服务协议。${NC}"
    echo -e "${YELLOW}   看到菜单栏出现鲸鱼图标即启动成功。${NC}"
    echo ""
    echo -e "${YELLOW}2. Docker 启动成功后，在终端执行:${NC}"
    echo "   docker compose build"
    echo "   docker compose run --rm bili-video --task basic_test"
    echo ""

elif [ "$OS" = "linux" ]; then
    # ============ Linux ============
    echo -e "${CYAN}[检测] Linux 系统${NC}"

    # 检测具体发行版
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        echo -e "${RED}[错误] 无法识别 Linux 发行版${NC}"
        exit 1
    fi

    echo -e "${YELLOW}[信息] 检测到发行版: $DISTRO${NC}"
    echo ""

    # 使用 Docker 官方一键安装脚本（国内镜像加速）
    echo -e "${CYAN}[安装] 正在安装 Docker Engine...${NC}"
    echo ""

    # 尝试官方脚本，失败则回退到包管理器
    if curl -fsSL https://get.docker.com | bash; then
        echo ""
        echo -e "${GREEN}[OK] Docker Engine 安装完成${NC}"
    else
        echo ""
        echo -e "${YELLOW}[备用] 官方脚本失败，使用包管理器安装...${NC}"

        case "$DISTRO" in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y docker.io docker-compose-v2
                ;;
            fedora)
                sudo dnf install -y docker docker-compose
                ;;
            centos|rhel)
                sudo yum install -y docker docker-compose
                ;;
            arch)
                sudo pacman -S --noconfirm docker docker-compose
                ;;
            *)
                echo -e "${RED}[错误] 不支持的发行版: $DISTRO${NC}"
                echo "请手动安装: https://docs.docker.com/engine/install/"
                exit 1
                ;;
        esac
        echo ""
        echo -e "${GREEN}[OK] Docker 安装完成${NC}"
    fi

    # 启动 Docker 服务
    echo ""
    echo -e "${CYAN}[服务] 启动 Docker 服务...${NC}"
    if command -v systemctl &> /dev/null; then
        sudo systemctl enable docker
        sudo systemctl start docker
    elif command -v service &> /dev/null; then
        sudo service docker start
    fi
    echo -e "${GREEN}[OK] Docker 服务已启动${NC}"

    # 将当前用户加入 docker 组（避免每次 sudo）
    if [ "$EUID" -ne 0 ]; then
        echo ""
        echo -e "${CYAN}[配置] 将当前用户加入 docker 组（免 sudo）...${NC}"
        sudo usermod -aG docker "$USER"
        echo -e "${YELLOW}[提示] 请注销并重新登录，或执行 'newgrp docker' 使配置生效${NC}"
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}   后续操作${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "  cd 到项目目录"
    echo "  docker compose build"
    echo "  docker compose run --rm bili-video --task basic_test"
    echo ""

else
    echo -e "${RED}[错误] 不支持的操作系统: $(uname -s)${NC}"
    echo "请手动安装: https://docs.docker.com/engine/install/"
    exit 1
fi
