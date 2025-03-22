# MedicalMan - 医疗管理系统

医疗管理系统是一个基于Flask的Web应用，用于医院管理和医疗数据分析。本系统提供医院运营数据的可视化和分析功能，支持基于大模型的智能查询，帮助医院管理者做出更明智的决策。

## 1. 功能特点

- **仪表盘**：直观展示医院关键绩效指标和运营概览
- **科室分析**：跟踪各科室工作量、收入和目标完成情况
- **DRG分析**：分析DRG分组、权重分值和成本控制情况
- **医生绩效**：评估医生工作效率、质量和患者满意度
- **患者分析**：分析患者来源、就诊频率和诊疗路径
- **财务分析**：监控收入、成本和利润指标
- **AI智能助手**：基于大模型的自然语言数据分析和问答
- **用户管理**：多级权限控制和用户行为审计

## 2. 技术架构

- **前端**：HTML, CSS, JavaScript, Bootstrap, Chart.js
- **后端**：Python 3.8+, Flask 2.0+
- **数据库**：SQLite 3
- **AI能力**：火山方舟API (深度求索大模型)
- **部署**：支持Docker容器化部署

## 3. 项目结构

```
medicalman/
├── app/                      # 应用核心代码
│   ├── models/               # 数据模型和数据库交互
│   ├── services/             # 业务逻辑服务
│   ├── controllers/          # 请求处理和路由控制
│   ├── presenters/           # 数据展示格式化
│   ├── utils/                # 工具函数和辅助方法
│   ├── config/               # 配置管理
│   └── prompts/              # AI大模型提示词模板
├── docs/                     # 项目文档和参考数据
│   ├── 医疗数据表.xlsx         # 示例数据和参考标准
│   └── 科室运营成本与医保临床路径建设版本.pdf # 业务参考文档
├── instance/                 # 实例特定文件（遵循Flask最佳实践）
│   └── medical_workload.db   # SQLite数据库文件
├── static/                   # 静态资源
│   ├── css/                  # 样式表
│   ├── js/                   # JavaScript文件
│   ├── images/               # 图片资源
│   └── uploads/              # 用户上传文件存储
├── templates/                # HTML模板
│   ├── dashboard/            # 仪表盘相关模板
│   ├── analysis/             # 分析页面模板
│   └── components/           # 可复用组件模板
├── tests/                    # 测试代码
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── migrations/               # 数据库迁移脚本
├── scripts/                  # 实用脚本
│   ├── import_data.py        # 数据导入脚本
│   └── generate_drg_data.py  # DRG测试数据生成
├── flask_session/           # Flask会话文件存储
├── .env              # 环境变量示例
├── .gitignore                # Git忽略配置
├── requirements.txt          # 项目依赖
├── run.py                    # 应用启动入口
└── README.md                 # 项目说明文档
```

## 4. 数据流程

1. **数据来源**：
   - Excel文件导入（通过`scripts/import_data.py`）
   - 系统手动录入
   - 测试数据生成（通过`scripts/generate_drg_data.py`）

2. **数据存储**：
   - 所有数据存储在`instance/medical_workload.db` SQLite数据库
   - 数据库包含门诊量、目标值、DRG记录等多个表

3. **数据处理**：
   - 由`app/services`中的服务组件处理业务逻辑
   - 统计分析由专门的分析服务执行

4. **数据展示**：
   - 通过`app/presenters`格式化数据
   - 在前端通过Chart.js进行可视化展示

## 5. 安装与部署

### 5.1 前提条件

- Python 3.8+
- pip (Python包管理器)
- Git (版本控制)

### 5.2 开发环境设置

1. **克隆代码库**
   ```bash
   git clone https://github.com/yourusername/medicalman.git
   cd medicalman
   ```

2. **创建并激活虚拟环境**
   ```bash
   # 创建虚拟环境
   python -m venv .venv
   
   # 激活虚拟环境（Windows）
   .venv\Scripts\activate
   
   # 激活虚拟环境（macOS/Linux）
   source .venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   
   # 编辑.env文件，设置必要的环境变量
   # FLASK_ENV=development
   # SECRET_KEY=your-secret-key
   # VOLCENGINE_API_KEY=your-api-key
   ```

5. **创建必要的目录**
   ```bash
   # 创建instance目录（数据库存储位置）
   mkdir -p instance
   
   # 创建上传文件目录
   mkdir -p static/uploads/documents
   ```

6. **初始化数据库并导入示例数据**
   ```bash
   # 导入示例数据
   python scripts/import_data.py
   
   # 生成DRG测试数据
   python scripts/generate_drg_data.py
   ```

7. **启动应用**
   ```bash
   # 开发模式启动
   python run.py
   ```

8. **访问应用**
   在浏览器中访问 http://localhost:5000

### 5.3 生产环境部署

对于生产环境，建议使用Gunicorn或uWSGI作为WSGI服务器，并配合Nginx作为前端代理。

```bash
# 安装生产依赖
pip install gunicorn

# 启动Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

## 6. 使用指南

### 6.1 登录系统

- **管理员账号**：admin
- **默认密码**：Admin123!
- 首次登录后请立即修改默认密码

### 6.2 数据管理

#### 6.2.1 数据导入

系统支持从Excel文件导入数据：
1. 准备符合格式的Excel文件或使用`docs`目录中的示例文件
2. 运行导入脚本：`python scripts/import_data.py`
3. 或通过Web界面上传数据文件

#### 6.2.2 DRG数据生成

系统支持生成DRG测试数据：
1. 运行生成脚本：`python scripts/generate_drg_data.py`
2. 脚本将使用`docs`目录中的参考数据生成DRG记录

### 6.3 AI智能助手

系统集成了基于大模型的AI智能助手：
1. 导航到"AI聊天"页面
2. 输入自然语言查询，如"近三个月内科门诊量趋势如何？"
3. 系统会自动分析查询，转换为SQL或直接从知识库回答
4. 可以通过聊天形式深入分析和探索数据

### 6.4 数据分析

1. **仪表盘**：展示关键指标概览
2. **专题分析**：深入分析特定领域数据
3. **自定义报表**：创建和保存自定义分析报表

## 7. 开发指南

### 7.1 项目架构

项目采用MCP (Model-Controller-Presenter) 架构：
- **Model**：数据模型和数据库操作
- **Controller**：处理请求和业务逻辑
- **Presenter**：格式化数据用于展示

### 7.2 数据库结构

- 数据库文件位于`instance/medical_workload.db`
- 主要表结构：
  - **门诊量**：记录各科室门诊就诊数据
  - **目标值**：各科室月度目标设定
  - **drg_records**：DRG分组相关记录
  - **doctors**：医生基本信息
  - **doctor_performance**：医生绩效记录
  - **patient_records**：患者就诊记录
  - **users**：系统用户信息

### 7.3 添加新功能

1. 在相应的模块中添加功能代码
2. 遵循项目架构和代码风格
3. 更新路由和控制器
4. 创建或修改模板
5. 添加单元测试和集成测试

## 8. 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 编写代码并添加测试
4. 提交更改 (`git commit -m 'Add some amazing feature'`)
5. 推送到分支 (`git push origin feature/amazing-feature`)
6. 创建Pull Request

## 9. 常见问题

### 9.1 数据库相关

**Q: 如何重置数据库？**  
A: 删除`instance/medical_workload.db`文件，然后重新运行导入脚本。

**Q: 如何备份数据库？**  
A: 复制`instance/medical_workload.db`文件到安全位置。

### 9.2 环境配置

**Q: 应用无法连接到AI服务？**  
A: 检查`.env`文件中的`VOLCENGINE_API_KEY`是否正确设置。

## 10. 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件
