#!/bin/bash

# 医疗指标平台启动脚本
# 作者: MedicalMan Team
# 版本: 1.0

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="医疗指标平台"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
RUN_FILE="$SCRIPT_DIR/run.py"

# 打印彩色日志
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印横幅
print_banner() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "    $PROJECT_NAME 启动脚本"
    echo "=================================="
    echo -e "${NC}"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "未找到Python环境，请安装Python 3.7+"
        exit 1
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    log_success "找到Python版本: $PYTHON_VERSION"
}

# 检查并创建虚拟环境
setup_venv() {
    log_info "检查虚拟环境..."
    
    if [ ! -d "$VENV_DIR" ]; then
        log_warning "虚拟环境不存在，正在创建..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        if [ $? -eq 0 ]; then
            log_success "虚拟环境创建成功"
        else
            log_error "虚拟环境创建失败"
            exit 1
        fi
    else
        log_success "虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        log_success "虚拟环境激活成功"
    else
        log_error "虚拟环境激活脚本不存在"
        exit 1
    fi
}

# 检查并安装依赖
install_dependencies() {
    log_info "检查项目依赖..."
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_error "requirements.txt文件不存在"
        exit 1
    fi
    
    # 检查是否需要安装依赖（简单检查Flask是否存在）
    if ! python -c "import flask" &> /dev/null; then
        log_warning "检测到缺少依赖，正在安装..."
        pip install -r "$REQUIREMENTS_FILE"
        if [ $? -eq 0 ]; then
            log_success "依赖安装完成"
        else
            log_error "依赖安装失败"
            exit 1
        fi
    else
        log_success "项目依赖已满足"
    fi
}

# 检查数据库
check_database() {
    log_info "检查数据库..."
    
    DB_DIR="$SCRIPT_DIR/instance"
    if [ ! -d "$DB_DIR" ]; then
        log_warning "数据库目录不存在，将在首次运行时创建"
    else
        log_success "数据库目录存在"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=${1:-5101}
    log_info "检查端口 $port..."
    
    if command -v ss &> /dev/null; then
        if ss -tlnp | grep -q ":$port "; then
            log_warning "端口 $port 已被占用"
            echo "尝试终止占用端口的进程..."
            
            # 查找并终止占用端口的Python进程
            PID=$(ss -tlnp | grep ":$port " | grep python | sed 's/.*pid=\([0-9]*\).*/\1/')
            if [ ! -z "$PID" ]; then
                kill $PID 2>/dev/null
                sleep 2
                log_success "已终止占用端口的进程 (PID: $PID)"
            fi
        else
            log_success "端口 $port 可用"
        fi
    fi
}

# 启动应用
start_application() {
    log_info "启动 $PROJECT_NAME..."
    
    if [ ! -f "$RUN_FILE" ]; then
        log_error "启动文件 run.py 不存在"
        exit 1
    fi
    
    echo ""
    log_success "🚀 正在启动应用..."
    log_info "访问地址: http://localhost:5101"
    log_info "按 Ctrl+C 停止应用"
    echo ""
    
    # 启动应用
    python "$RUN_FILE"
}

# 主函数
main() {
    print_banner
    
    # 切换到项目目录
    cd "$SCRIPT_DIR"
    log_info "切换到项目目录: $SCRIPT_DIR"
    
    # 检查环境
    check_python
    setup_venv
    activate_venv
    install_dependencies
    check_database
    check_port 5101
    
    echo ""
    log_success "✅ 环境检查完成，准备启动应用"
    echo ""
    
    # 启动应用
    start_application
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -c, --check    仅检查环境，不启动应用"
    echo "  -r, --reset    重新创建虚拟环境"
    echo ""
    echo "示例:"
    echo "  $0              # 启动应用"
    echo "  $0 --check      # 检查环境"
    echo "  $0 --reset      # 重置环境"
}

# 仅检查环境
check_only() {
    print_banner
    cd "$SCRIPT_DIR"
    
    check_python
    setup_venv
    activate_venv
    install_dependencies
    check_database
    
    log_success "✅ 环境检查完成"
}

# 重置环境
reset_environment() {
    print_banner
    cd "$SCRIPT_DIR"
    
    log_warning "重置虚拟环境..."
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
        log_success "已删除旧的虚拟环境"
    fi
    
    setup_venv
    activate_venv
    install_dependencies
    
    log_success "✅ 环境重置完成"
}

# 处理命令行参数
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    -c|--check)
        check_only
        exit 0
        ;;
    -r|--reset)
        reset_environment
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac
