# 🚀 混合Agent架构 - 快速部署指南

## ✅ 部署检查清单

### 1. 核心文件验证
确认以下文件已正确添加到项目中：

```
app/services/enhanced_query_service.py     ✅ 核心增强查询服务
app/config/enhanced_config.py              ✅ 增强配置文件  
app/routes/ai_chat_routes.py               ✅ 已更新路由文件
app/services/chart_service.py              ✅ 已增强图表服务
test_enhanced_system.py                    ✅ 测试脚本
ENHANCED_SYSTEM_README.md                  ✅ 功能说明文档
```

### 2. 依赖检查
确认以下Python包已安装：
```bash
# LangChain相关（项目中已有）
langchain>=0.3.21
langchain-community>=0.3.20
langchain-core>=0.3.47

# 数据处理（项目中已有）
pandas>=2.2.0
numpy>=1.26.3

# 向量数据库（项目中已有）
faiss-cpu  # 或 faiss-gpu
```

### 3. 环境配置检查
确认以下环境变量已设置：
```bash
# .env 文件中
VOLCENGINE_API_KEY=your_api_key
VOLCENGINE_API_URL=your_api_url  
VOLCENGINE_MODEL=deepseek-v3-241226
```

## 🔄 启用混合架构

### 方法1：已自动启用
路由文件 `app/routes/ai_chat_routes.py` 已自动更新，新的查询将使用混合架构。

### 方法2：手动验证切换
如果需要手动验证切换，检查以下代码：

```python
# app/routes/ai_chat_routes.py 第82-84行
# 应该是这样：
result = enhanced_query_service.process_enhanced_query(query, knowledge_settings, attachments)

# 而不是原来的：
# result = process_user_query(query, knowledge_settings, attachments)
```

### 方法3：渐进式部署
如果希望渐进式部署，可以添加开关控制：

```python
# app/routes/ai_chat_routes.py
USE_ENHANCED_SYSTEM = True  # 控制开关

if USE_ENHANCED_SYSTEM:
    result = enhanced_query_service.process_enhanced_query(query, knowledge_settings, attachments)
else:
    result = process_user_query(query, knowledge_settings, attachments)
```

## 🧪 功能测试

### 1. 运行测试脚本
```bash
cd /home/alfred/multiproject/医疗指标平台/medicalman
python test_enhanced_system.py
```

### 2. 手动测试不同复杂度查询

#### 简单查询测试
```
用户输入：查看数据库中有哪些表
预期行为：快速路由处理，1-2秒响应
预期输出：包含complexity: "simple"
```

#### 中等查询测试  
```
用户输入：分析各科室本月门诊量并生成图表
预期行为：增强路由处理，2-5秒响应
预期输出：包含图表数据和complexity: "moderate"
```

#### 复杂查询测试
```
用户输入：综合分析医院运营状况并提供改进建议
预期行为：Agent模式处理，5-15秒响应
预期输出：详实分析内容和complexity: "complex"
```

### 3. API测试
```bash
# 使用curl测试API端点
curl -X POST http://localhost:5000/chat/query \
-H "Content-Type: application/json" \
-d '{
  "query": "分析内科门诊量趋势",
  "knowledge_settings": {},
  "attachments": []
}'
```

## 🔧 配置调优

### 1. 复杂度阈值调整
如果复杂度判断不够准确，可以调整阈值：

```python
# app/config/enhanced_config.py
COMPLEXITY_ANALYSIS_CONFIG = {
    "confidence_thresholds": {
        "simple": 0.8,    # 提高简单查询阈值
        "moderate": 0.6,  # 保持中等查询阈值
        "complex": 0.4    # 降低复杂查询阈值  
    }
}
```

### 2. 图表颜色主题定制
```python
# app/config/enhanced_config.py
CHART_ENHANCEMENT_CONFIG = {
    "color_schemes": {
        "medical_primary": [
            '#您的主色调',
            '#您的辅色调', 
            # ... 更多颜色
        ]
    }
}
```

### 3. Agent工具超时设置
```python
# app/config/enhanced_config.py
AGENT_TOOLS_CONFIG = {
    "execution_timeout": 45,    # 增加到45秒
    "max_retries": 3,           # 增加重试次数
}
```

## 📊 监控和调试

### 1. 日志监控
增强系统会产生详细日志，关注以下日志：
```
查询复杂度分析: complexity.value, confidence: X.X
使用快速路由处理简单查询
Agent模式处理复杂查询，需要执行步骤: [...]
智能生成了 X 个图表
```

### 2. 性能监控
在响应中查看性能指标：
```json
{
  "processing_info": {
    "complexity": "moderate",
    "process_time": "3.2秒",
    "reasoning": "分析原因"
  }
}
```

### 3. 错误处理
如果遇到错误，检查：
1. LLM API连接状态
2. 数据库连接状态  
3. 依赖包版本兼容性

## 🚨 故障排除

### 常见问题及解决方案

#### 1. "enhanced_query_service"导入错误
```python
# 确认文件路径正确
from app.services.enhanced_query_service import enhanced_query_service
```

#### 2. 复杂度分析不准确
```python
# 检查LLM API连接
# 调整置信度阈值
# 查看日志中的分析推理过程
```

#### 3. Agent执行超时
```python
# 增加超时时间
# 检查各工具服务状态
# 简化执行步骤
```

#### 4. 图表生成失败
```python
# 检查数据格式
# 验证图表服务状态
# 查看图表配置日志
```

## 🔄 回滚方案

如果需要临时回滚到原系统：

### 1. 快速回滚
```python
# app/routes/ai_chat_routes.py
# 修改第82-84行为：
result = process_user_query(query, knowledge_settings, attachments)
```

### 2. 保留增强功能的部分回滚
```python
# 只使用增强的图表功能，其他保持原样
if "图表" in query or "分析" in query:
    result = enhanced_query_service.process_enhanced_query(query, knowledge_settings, attachments)
else:
    result = process_user_query(query, knowledge_settings, attachments)
```

## 📈 生产环境建议

### 1. 性能优化
- 启用查询结果缓存
- 配置负载均衡
- 监控API调用频率

### 2. 安全设置
- 设置API调用限制
- 添加查询内容过滤
- 配置错误信息脱敏

### 3. 监控告警
- 设置响应时间告警
- 监控错误率
- 跟踪用户满意度

## ✅ 部署完成验证

部署完成后，验证以下功能：

- [ ] 简单查询响应正常且快速
- [ ] 中等查询生成合适图表
- [ ] 复杂查询提供详实分析
- [ ] 图表显示清晰美观
- [ ] 内容结构完整详实
- [ ] API响应格式正确
- [ ] 错误处理机制正常

---

**恭喜！🎉 混合Agent架构部署完成，您的医疗指标平台现已具备更强大的智能分析能力！**
