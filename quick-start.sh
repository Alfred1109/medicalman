#!/bin/bash

# 医疗指标平台快速启动脚本
# 适合开发环境快速启动，跳过环境检查

# 设置颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 医疗指标平台 - 快速启动${NC}"
echo ""

# 切换到项目目录
cd "$SCRIPT_DIR"

# 激活虚拟环境并启动
if [ -f "venv/bin/activate" ]; then
    echo -e "${GREEN}激活虚拟环境...${NC}"
    source venv/bin/activate
    
    echo -e "${GREEN}启动应用...${NC}"
    echo "访问地址: http://localhost:5101"
    echo "按 Ctrl+C 停止应用"
    echo ""
    
    python run.py
else
    echo "❌ 虚拟环境不存在，请先运行: ./start.sh"
    exit 1
fi
