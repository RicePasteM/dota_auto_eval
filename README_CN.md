<p align="center">
  <img src="manage_frontend/public/favicon.ico" width="64" height="64" alt="DOTA Auto Eval  Logo">
</p>

<h1 align="center">DOTA Auto Eval</h1>

<p align="center">
  <a href="https://github.com/RicePasteM/dota_auto_eval">
    <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  </a>
  <a href="https://github.com/RicePasteM/dota_auto_eval/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.8+-orange.svg" alt="Python">
  </a>
</p>

<p align="center">
  DOTA Auto Eval 是一个自动化的 DOTA（Detection Object in Aerial Images）评估系统，专门用于解决 DOTA 官方验证服务器提交次数限制的问题。系统通过自动化邮箱注册和账号管理，实现了验证文件的自动提交和结果收集，显著提升了模型调试效率。
</p>

---

## ✨ 主要功能

| 功能 | 描述 |
|------|------|
| 📧 **邮箱自动化** | 基于 smailpro 的批量临时邮箱注册，验证码自动获取，邮箱状态监控 |
| 👤 **账号管理** | DOTA 验证服务器账号自动注册，账号激活自动化处理，多账号轮换使用 |
| 📤 **提交自动化** | 验证文件自动提交，结果自动收集与解析，提交限制智能规避 |

---

## 🏗️ 项目架构

```
DOTA_Auto_Eval/
├── app_backend/       # 应用后端服务
├── manage_frontend/   # 管理系统前端（预编译）
├── python_package/    # 自动化工具包
└── temp/             # 临时文件目录
```

---

## 📦 主要模块

### 1. 管理系统前端 🖥️

基于 Vue 3 的现代化 Web 管理界面，提供：
- 📧 邮箱和账号管理
- 📊 提交任务监控
- 📈 评估结果展示
- 🔄 系统状态实时监控

**技术栈：** Vue 3 • Element Plus • ECharts • Vite

> **注意**：前端在上传前已预先编译好，后端会自动加载并提供前端服务。只有在需要修改前端代码时才需要安装 Node.js。

### 2. 应用后端 ⚙️

系统的核心服务端，负责：
- 📧 邮箱注册和管理
- 🤖 DOTA 账号自动创建
- 📋 提交任务调度
- 📥 结果自动获取

### 3. Python 工具包 🐍

提供核心的自动化功能：
- 📤 提交验证文件到 DOTA 服务器
- 🤖 账号注册自动化
- 📊 结果获取和解析
- ⚡ 错误处理和重试机制

---

## 📋 系统要求

| 需求 | 版本 | 备注 |
|------|------|------|
| 🐍 Python | 3.8+ | 后端运行环境 |
| 🌐 Node.js | 16.0.0+ | 仅用于前端开发 |
| 📦 npm | 7.0.0+ | 仅用于前端开发 |
| 🌍 浏览器 | 现代浏览器 | Chrome, Firefox, Safari, Edge |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/RicePasteM/dota_auto_eval
cd DOTA_Auto_Eval
```

### 2. 启动后端服务

```bash
cd app_backend
pip install -r requirements.txt
python wsgi.py
```

### 3. 访问系统

打开浏览器并访问后端服务地址（默认为 `http://localhost:5000`）

> 📖 详细部署说明请参考 **[部署指南](部署指南.md)**。

---

## 📖 使用指南

### 1. 账号管理
- 🔧 设置验证服务器地址
- 🔧 设置账号生成规则
- ⚙️ 配置自动注册参数
- 👁️ 监控账号状态

### 2. 提交管理
- 📤 上传验证文件
- ⚙️ 设置提交策略
- 📊 查看评估结果

---

## 💻 开发指南

| 领域 | 指南 |
|------|------|
| 🎨 前端 | 遵循 Vue 3 组合式 API 最佳实践，使用 Element Plus 组件库 |
| ⚙️ 后端 | 遵循 PEP 8 编码规范，编写单元测试，维护 API 文档 |
| 🐍 工具包 | 保持代码模块化，完善错误处理，优化自动化流程 |

---

## ⚠️ 注意事项

- 📧 合理使用临时邮箱服务，避免滥用
- 📜 遵守 DOTA 官方服务器使用规则
- 🧹 定期清理临时文件
- ✅ 及时处理失败任务

---

## 📄 许可证

MIT

---

<p align="center">
  <a href="README.md">🇺🇸 English Version</a>
</p>
