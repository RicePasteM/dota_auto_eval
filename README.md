<p align="center">
  <img src="manage_frontend/public/favicon.ico" width="64" height="64" alt="DOTA Auto Eval Logo">
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
  DOTA Auto Eval is an automated evaluation system for DOTA (Detection Object in Aerial Images), designed to address the limited submission quota on the DOTA official validation server. The system achieves automated email registration and account management, enabling automatic submission of validation files and result collection, significantly improving model debugging efficiency.
</p>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📧 **Email Automation** | Batch temporary email registration via smailpro, automatic verification code retrieval, email status monitoring |
| 👤 **Account Management** | Automated DOTA validation server account registration, automated activation processing, multi-account rotation |
| 📤 **Submission Automation** | Automatic validation file submission, automatic result collection and parsing, intelligent submission limit avoidance |

---

## 🏗️ Project Structure

```
DOTA_Auto_Eval/
├── app_backend/       # Application backend service
├── manage_frontend/   # Management system frontend (pre-compiled)
├── python_package/    # Automation toolkit
└── temp/             # Temporary file directory
```

---

## 📦 Main Modules

### 1. Management Frontend 🖥️

A modern web management interface built with Vue 3, providing:
- 📧 Email and account management
- 📊 Submission task monitoring
- 📈 Evaluation results display
- 🔄 Real-time system status monitoring

**Tech Stack:** Vue 3 • Element Plus • ECharts • Vite

> **Note:** The frontend is pre-compiled and served by the backend automatically. Node.js is only required if you need to modify the frontend code.

### 2. Application Backend ⚙️

The core server-side of the system, responsible for:
- 📧 Email registration and management
- 🤖 Automated DOTA account creation
- 📋 Submission task scheduling
- 📥 Automatic result retrieval

### 3. Python Package 🐍

Provides core automation functionality:
- 📤 Submit validation files to DOTA server
- 🤖 Automated account registration
- 📊 Result retrieval and parsing
- ⚡ Error handling and retry mechanisms

---

## 📋 System Requirements

| Requirement | Version | Note |
|-------------|---------|------|
| 🐍 Python | 3.8+ | Backend runtime |
| 🌐 Node.js | 16.0.0+ | Only for frontend development |
| 📦 npm | 7.0.0+ | Only for frontend development |
| 🌍 Browser | Modern | Chrome, Firefox, Safari, Edge |

---

## 🚀 Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/RicePasteM/dota_auto_eval
cd DOTA_Auto_Eval
```

### 2. Start the Backend Service

```bash
cd app_backend
pip install -r requirements.txt
python wsgi.py
```

### 3. Access the System

Open your browser and navigate to the backend service address (default: `http://localhost:5000`)

> 📖 For detailed deployment instructions, please refer to the **[Deployment Guide](Deployment_Guide.md)**.

---

## 📖 Usage Guide

### 1. Account Management
- 🔧 Set validation server address
- 🔧 Set account generation rules
- ⚙️ Configure automatic registration parameters
- 👁️ Monitor account status

### 2. Submission Management
- 📤 Upload validation files
- ⚙️ Set submission strategies
- 📊 View evaluation results

---

## 💻 Development Guide

| Area | Guidelines |
|------|------------|
| 🎨 Frontend | Follow Vue 3 Composition API best practices, use Element Plus component library |
| ⚙️ Backend | Follow PEP 8 coding standards, write unit tests, maintain API documentation |
| 🐍 Package | Keep code modular, improve error handling, optimize automation workflows |

---

## ⚠️ Notes

- 📧 Use temporary email services reasonably to avoid abuse
- 📜 Comply with DOTA official server usage rules
- 🧹 Clean up temporary files regularly
- ✅ Handle failed tasks promptly

---

## 📄 License

MIT

---

<p align="center">
  <a href="README_CN.md">🇨🇳 中文版</a>
</p>
