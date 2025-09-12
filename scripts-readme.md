# 医疗指标平台 - 启动脚本说明

## 📋 脚本概览

本项目提供了一套完整的Shell脚本来管理医疗指标平台的启动、停止和状态检查。

### 🚀 脚本列表

| 脚本名称 | 功能说明 | 使用场景 |
|----------|----------|----------|
| `start.sh` | 完整启动脚本 | 首次运行、生产环境 |
| `quick-start.sh` | 快速启动脚本 | 开发环境、快速测试 |
| `stop.sh` | 停止脚本 | 正常停止应用 |
| `status.sh` | 状态检查脚本 | 监控、故障排查 |

## 🔧 使用方法

### 1. 完整启动（推荐首次使用）

```bash
./start.sh
```

**功能：**
- ✅ 检查Python环境
- ✅ 自动创建虚拟环境
- ✅ 安装项目依赖
- ✅ 检查数据库状态
- ✅ 检查端口占用
- ✅ 启动应用

**可选参数：**
```bash
./start.sh --help      # 显示帮助
./start.sh --check     # 仅检查环境
./start.sh --reset     # 重新创建虚拟环境
```

### 2. 快速启动（开发环境）

```bash
./quick-start.sh
```

**功能：**
- 跳过环境检查（适合开发）
- 直接激活虚拟环境并启动
- 启动速度更快

### 3. 停止应用

```bash
./stop.sh
```

**功能：**
- 优雅停止所有应用进程
- 释放占用的端口
- 检查停止状态

**可选参数：**
```bash
./stop.sh --help       # 显示帮助
./stop.sh --force      # 强制停止所有相关进程
```

### 4. 状态检查

```bash
./status.sh
```

**功能：**
- 检查应用进程状态
- 检查端口监听状态
- 检查Web服务响应
- 检查虚拟环境
- 检查数据库文件
- 检查日志文件
- 显示系统信息

**可选参数：**
```bash
./status.sh --help     # 显示帮助
./status.sh --quick    # 快速检查（仅进程和端口）
```

## 💡 使用示例

### 完整的启动流程

```bash
# 1. 首次启动（会自动配置环境）
./start.sh

# 2. 检查运行状态
./status.sh

# 3. 停止应用
./stop.sh

# 4. 快速重启
./quick-start.sh
```

### 开发环境工作流

```bash
# 开发时快速启动
./quick-start.sh

# 检查状态
./status.sh --quick

# 开发完成后停止
./stop.sh
```

### 问题排查

```bash
# 详细状态检查
./status.sh

# 如果有问题，强制停止
./stop.sh --force

# 重置环境
./start.sh --reset
```

## 🌐 访问地址

启动成功后，可通过以下地址访问：

- **本地访问：** http://localhost:5101
- **局域网访问：** http://YOUR_IP:5101

### 默认登录信息

- **管理员账户**
  - 用户名：`admin`
  - 密码：`Admin123!`

- **普通管理员**
  - 用户名：`manager`  
  - 密码：`Manager123!`

- **数据分析师**
  - 用户名：`analyst`
  - 密码：`Analyst123!`

## 📁 目录结构

```
医疗指标平台/medicalman/
├── start.sh           # 完整启动脚本
├── quick-start.sh      # 快速启动脚本
├── stop.sh             # 停止脚本
├── status.sh           # 状态检查脚本
├── run.py              # 应用入口文件
├── requirements.txt    # 依赖包列表
├── venv/               # Python虚拟环境
├── instance/           # 数据库文件
├── logs/               # 日志文件
└── app/                # 应用源码
```

## 🔍 常见问题

### Q: 首次运行提示权限错误
A: 执行以下命令给脚本添加执行权限：
```bash
chmod +x *.sh
```

### Q: 端口被占用
A: 使用强制停止命令：
```bash
./stop.sh --force
```

### Q: 虚拟环境有问题
A: 重置虚拟环境：
```bash
./start.sh --reset
```

### Q: 应用无法访问
A: 检查防火墙设置，确保5101端口开放：
```bash
# Ubuntu/Debian
sudo ufw allow 5101

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5101/tcp
sudo firewall-cmd --reload
```

### Q: 检查应用是否正常运行
A: 使用状态检查脚本：
```bash
./status.sh
```

## 📊 脚本输出说明

### 颜色编码
- 🔵 **蓝色 [INFO]** - 信息提示
- 🟢 **绿色 [SUCCESS]** - 操作成功
- 🟡 **黄色 [WARNING]** - 警告信息
- 🔴 **红色 [ERROR]** - 错误信息

### 状态检查结果
- ✅ **所有检查通过** - 系统运行正常
- ⚠️ **部分检查通过** - 系统运行但可能有问题
- ❌ **多数检查失败** - 系统可能未正常运行

## 🛠 高级用法

### 后台运行
```bash
nohup ./quick-start.sh > app.log 2>&1 &
```

### 定时检查
添加到crontab进行定时检查：
```bash
# 每5分钟检查一次状态
*/5 * * * * /path/to/status.sh --quick
```

### 系统服务
可以将启动脚本配置为系统服务，实现开机自启：
```bash
# 创建服务文件
sudo nano /etc/systemd/system/medical-platform.service

# 启用服务
sudo systemctl enable medical-platform
sudo systemctl start medical-platform
```

## 📞 技术支持

如果在使用过程中遇到问题，请：

1. 首先运行 `./status.sh` 检查详细状态
2. 查看日志文件：`tail -f logs/medical_workload.log.1`
3. 尝试重置环境：`./start.sh --reset`

---

*最后更新时间：2025年9月*
