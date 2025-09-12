#!/bin/bash

# 医疗指标平台停止脚本
# 作者: MedicalMan Team

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 停止应用
stop_application() {
    log_info "正在停止医疗指标平台..."
    
    # 查找并终止Python进程
    PIDS=$(pgrep -f "python.*run.py")
    
    if [ -z "$PIDS" ]; then
        log_warning "未找到运行中的应用进程"
        return 0
    fi
    
    for PID in $PIDS; do
        log_info "终止进程 PID: $PID"
        kill $PID
        
        # 等待进程结束
        sleep 2
        
        # 如果进程仍然存在，强制杀死
        if kill -0 $PID 2>/dev/null; then
            log_warning "强制终止进程 PID: $PID"
            kill -9 $PID
        fi
    done
    
    log_success "✅ 应用已停止"
}

# 检查端口状态
check_port() {
    local port=${1:-5101}
    
    if command -v ss &> /dev/null; then
        if ss -tlnp | grep -q ":$port "; then
            log_warning "端口 $port 仍被占用"
            return 1
        else
            log_success "端口 $port 已释放"
            return 0
        fi
    fi
}

# 主函数
main() {
    echo -e "${BLUE}=================================="
    echo "    医疗指标平台 停止脚本"
    echo "==================================${NC}"
    echo ""
    
    stop_application
    
    # 检查端口状态
    sleep 1
    check_port 5101
    
    echo ""
    log_success "🛑 医疗指标平台已完全停止"
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -f, --force    强制停止所有相关进程"
    echo ""
}

# 强制停止
force_stop() {
    echo -e "${RED}⚠️  强制停止模式${NC}"
    echo ""
    
    # 停止所有Python Flask进程
    log_info "查找所有Python Flask进程..."
    FLASK_PIDS=$(pgrep -f "python.*flask\|flask.*run\|python.*run.py")
    
    if [ ! -z "$FLASK_PIDS" ]; then
        for PID in $FLASK_PIDS; do
            log_info "强制终止Flask进程 PID: $PID"
            kill -9 $PID 2>/dev/null
        done
    fi
    
    # 释放5101端口
    log_info "释放端口 5101..."
    PORT_PIDS=$(ss -tlnp | grep ":5101 " | sed 's/.*pid=\([0-9]*\).*/\1/' | tr ',' '\n' | grep -o '[0-9]*')
    
    if [ ! -z "$PORT_PIDS" ]; then
        for PID in $PORT_PIDS; do
            if [ ! -z "$PID" ]; then
                log_info "强制终止占用端口的进程 PID: $PID"
                kill -9 $PID 2>/dev/null
            fi
        done
    fi
    
    sleep 2
    check_port 5101
    
    log_success "🛑 强制停止完成"
}

# 处理命令行参数
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    -f|--force)
        force_stop
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
