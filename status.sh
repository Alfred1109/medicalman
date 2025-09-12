#!/bin/bash

# 医疗指标平台状态检查脚本

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

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 打印横幅
echo -e "${BLUE}=================================="
echo "    医疗指标平台 状态检查"
echo "==================================${NC}"
echo ""

# 检查应用进程
check_process() {
    log_info "检查应用进程..."
    
    PIDS=$(pgrep -f "python.*run.py")
    if [ ! -z "$PIDS" ]; then
        log_success "应用正在运行 (PID: $PIDS)"
        return 0
    else
        log_warning "应用未运行"
        return 1
    fi
}

# 检查端口
check_port() {
    local port=${1:-5101}
    log_info "检查端口 $port..."
    
    if command -v ss &> /dev/null; then
        if ss -tlnp | grep -q ":$port "; then
            log_success "端口 $port 正在监听"
            return 0
        else
            log_warning "端口 $port 未被监听"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tlnp | grep -q ":$port "; then
            log_success "端口 $port 正在监听"
            return 0
        else
            log_warning "端口 $port 未被监听"
            return 1
        fi
    else
        log_error "无法检查端口状态（ss或netstat命令不可用）"
        return 1
    fi
}

# 检查网络连接
check_web() {
    log_info "检查Web服务..."
    
    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5101 | grep -q "200\|302"; then
            log_success "Web服务响应正常"
            return 0
        else
            log_warning "Web服务无响应"
            return 1
        fi
    else
        log_warning "curl命令不可用，无法测试Web服务"
        return 1
    fi
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."
    
    if [ -d "$SCRIPT_DIR/venv" ]; then
        log_success "虚拟环境存在"
        return 0
    else
        log_error "虚拟环境不存在"
        return 1
    fi
}

# 检查数据库
check_database() {
    log_info "检查数据库..."
    
    DB_FILE="$SCRIPT_DIR/instance/medical_workload.db"
    if [ -f "$DB_FILE" ]; then
        DB_SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
        log_success "数据库文件存在 (大小: $DB_SIZE)"
        return 0
    else
        log_warning "数据库文件不存在"
        return 1
    fi
}

# 检查日志
check_logs() {
    log_info "检查日志文件..."
    
    LOG_DIR="$SCRIPT_DIR/logs"
    if [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR)" ]; then
        LOG_COUNT=$(ls -1 "$LOG_DIR" | wc -l)
        log_success "日志目录存在，包含 $LOG_COUNT 个文件"
        
        # 显示最新日志文件
        LATEST_LOG=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)
        if [ ! -z "$LATEST_LOG" ]; then
            LOG_NAME=$(basename "$LATEST_LOG")
            LOG_SIZE=$(ls -lh "$LATEST_LOG" | awk '{print $5}')
            log_info "最新日志: $LOG_NAME (大小: $LOG_SIZE)"
        fi
        return 0
    else
        log_warning "日志目录为空或不存在"
        return 1
    fi
}

# 显示系统信息
show_system_info() {
    echo ""
    log_info "系统信息:"
    echo "  项目目录: $SCRIPT_DIR"
    echo "  Python版本: $(python3 --version 2>&1 || echo '未找到Python3')"
    echo "  系统时间: $(date)"
    echo "  运行时长: $(uptime -p 2>/dev/null || echo '无法获取')"
}

# 主函数
main() {
    cd "$SCRIPT_DIR"
    
    # 执行所有检查
    TOTAL_CHECKS=6
    PASSED_CHECKS=0
    
    check_process && ((PASSED_CHECKS++))
    check_port 5101 && ((PASSED_CHECKS++))
    check_web && ((PASSED_CHECKS++))
    check_venv && ((PASSED_CHECKS++))
    check_database && ((PASSED_CHECKS++))
    check_logs && ((PASSED_CHECKS++))
    
    echo ""
    echo "=================================="
    
    if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
        log_success "✅ 所有检查通过 ($PASSED_CHECKS/$TOTAL_CHECKS)"
        echo -e "${GREEN}🎉 医疗指标平台运行状态良好${NC}"
    elif [ $PASSED_CHECKS -gt 2 ]; then
        log_warning "⚠️  部分检查通过 ($PASSED_CHECKS/$TOTAL_CHECKS)"
        echo -e "${YELLOW}🔧 医疗指标平台运行但可能有问题${NC}"
    else
        log_error "❌ 多数检查失败 ($PASSED_CHECKS/$TOTAL_CHECKS)"
        echo -e "${RED}🚨 医疗指标平台可能未正常运行${NC}"
    fi
    
    show_system_info
    
    echo ""
    echo "访问地址: http://localhost:5101"
    echo "=================================="
}

# 快速检查模式
quick_check() {
    if check_process && check_port 5101; then
        echo -e "${GREEN}✅ 医疗指标平台正在运行${NC}"
        exit 0
    else
        echo -e "${RED}❌ 医疗指标平台未运行${NC}"
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -q, --quick    快速检查（仅检查进程和端口）"
    echo ""
}

# 处理命令行参数
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    -q|--quick)
        quick_check
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
