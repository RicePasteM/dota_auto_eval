# DOTA Auto Eval 系统

DOTA Auto Eval 是一个自动化的DOTA（Detection Object in Aerial Images）评估系统，专门用于解决DOTA官方验证服务器提交次数限制的问题。系统通过自动化邮箱注册和账号管理，实现了验证文件的自动提交和结果收集，显著提升了模型调试效率。

## 主要功能

1. 邮箱自动化
   - 基于smailpro的批量临时邮箱注册
   - 邮箱验证码自动获取
   - 邮箱状态监控

2. 账号管理
   - DOTA验证服务器账号自动注册
   - 账号激活自动化处理
   - 多账号轮换使用

3. 提交自动化
   - 验证文件自动提交
   - 结果自动收集与解析
   - 提交限制智能规避

## 项目架构

```
DOTA_Auto_Eval/
├── app_backend/      # 应用后端服务
├── manage_frontend/  # 管理系统前端
├── python_package/   # 自动化工具包
└── temp/            # 临时文件目录
```

## 主要模块说明

### 1. 管理系统前端 (manage_frontend)

基于Vue 3的现代化Web管理界面，提供：
- 邮箱和账号管理
- 提交任务监控
- 评估结果展示
- 系统状态实时监控

技术栈：
- Vue 3
- Element Plus
- ECharts
- Vite

### 2. 应用后端 (app_backend)

系统的核心服务端，负责：
- 邮箱注册和管理
- DOTA账号自动创建
- 提交任务调度
- 结果自动获取

### 3. Python工具包 (python_package)

提供核心的自动化功能：
- 提交验证文件到DOTA服务器
- 账号注册自动化
- 结果获取和解析
- 错误处理和重试机制

## 系统要求

- Python 3.8+
- Node.js 16.0.0+
- npm 7.0.0+
- 现代浏览器（Chrome, Firefox, Safari, Edge等）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/RicePasteM/dota_auto_eval
cd DOTA_Auto_Eval
```

### 2. 启动管理前端

```bash
cd manage_frontend
npm install
npm run dev
```

### 3. 启动后端服务

```bash
cd app_backend
pip install -r requirements.txt
python wsgi.py
```

## 使用指南

1. 账号管理
   - 设置验证服务器地址
   - 设置账号生成规则
   - 配置自动注册参数
   - 监控账号状态

2. 提交管理
   - 上传验证文件
   - 设置提交策略
   - 查看评估结果

## 开发指南

1. 前端开发
   - 遵循Vue 3组合式API最佳实践
   - 使用Element Plus组件库
   - 参考前端模块的具体README

2. 后端开发
   - 遵循PEP 8编码规范
   - 编写单元测试
   - 注意API文档维护

3. 工具包开发
   - 保持代码模块化
   - 完善错误处理
   - 优化自动化流程

## 注意事项

- 合理使用临时邮箱服务，避免滥用
- 遵守DOTA官方服务器使用规则
- 定期清理临时文件
- 及时处理失败任务

## 许可证

MIT

## 联系方式

HuZhangchi@mail.ustc.edu.cn