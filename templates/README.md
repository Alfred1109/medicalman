# 模板目录结构说明

## 目录结构

```
templates/
├── base.html                # 基础模板
├── components/             # 可复用组件
│   ├── layout/            # 布局组件
│   ├── forms/             # 表单组件
│   ├── charts/            # 图表组件
│   ├── tables/            # 表格组件
│   ├── modals/            # 模态框组件
│   └── widgets/           # 小部件组件
├── auth/                  # 认证相关页面
├── dashboard/             # 仪表盘相关页面
├── analysis/              # 分析相关页面
├── settings/              # 设置相关页面
├── ai_chat/              # AI聊天相关页面
├── reports/              # 报告相关页面
├── main/                 # 主要页面
├── api/                  # API相关页面
└── errors/               # 错误页面
```

## 组件使用说明

### 布局组件
- `layout/header.html`: 页面头部组件
  ```jinja
  {% include 'components/layout/header.html' %}
  ```

### 表格组件
- `tables/data_table.html`: 数据表格组件
  ```jinja
  {% from 'components/tables/data_table.html' import data_table %}
  {{ data_table(headers=['列1', '列2'], rows=data_rows) }}
  ```

### 图表组件
- `charts/chart_container.html`: 图表容器组件
  ```jinja
  {% from 'components/charts/chart_container.html' import chart_container %}
  {{ chart_container('chart1', '图表标题', '图表描述') }}
  ```

### 表单组件
- `forms/form_group.html`: 表单组组件
  ```jinja
  {% from 'components/forms/form_group.html' import form_group %}
  {{ form_group('用户名', 'username', required=true) }}
  ```

### 模态框组件
- `modals/modal.html`: 模态框组件
  ```jinja
  {% from 'components/modals/modal.html' import modal %}
  {% call modal('modal1', '模态框标题') %}
    模态框内容
  {% endcall %}
  ```

### 小部件组件
- `widgets/stat_card.html`: 统计卡片组件
  ```jinja
  {% from 'components/widgets/stat_card.html' import stat_card %}
  {{ stat_card('总收入', '¥100,000', '本月收入统计', 5.2) }}
  ```

## 开发规范

1. 模板继承
   - 所有页面应继承自 `base.html`
   - 使用适当的块（block）进行内容覆盖

2. 组件复用
   - 优先使用现有组件
   - 新组件应放在对应的组件目录中

3. 命名规范
   - 文件名使用小写字母和连字符
   - 模板块名称使用下划线
   - 组件宏名称使用小写字母和下划线

4. 注释规范
   - 为复杂的模板块添加注释
   - 组件使用示例应包含在文档中

5. 样式规范
   - 使用 Tailwind CSS 类名
   - 避免内联样式
   - 保持一致的样式命名 