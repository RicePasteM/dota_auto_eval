# DOTA Auto Eval Deployment Guide

This guide will help you deploy the DOTA Auto Eval system.

---

## 1. Configure Database

### Using SQLite (Default)

By default, the system uses SQLite database. No additional configuration is required.

Edit the `.env` file:

```env
DB_TYPE=sqlite
```

### Using MySQL

If you need to use MySQL database:

Edit the `.env` file:

```env
DB_TYPE=mysql
DATABASE_URI=mysql://username:password@host:port/database_name
```

---

## 2. First Start and Accept EULA

Run the startup script:

```bash
cd app_backend
.\start.bat
```

On first startup, the system will:
1. Automatically create `eula.txt` file (content: `False`)
2. Display the End User License Agreement (EULA)
3. Prompt you to accept the agreement and restart

**Press Ctrl+C to exit the program**

Edit the `eula.txt` file and change the content to `True`:

```txt
True
```

---

## 3. Start Again and Configure SYSTEM_API_KEY

Run the startup script again:

```bash
.\start.bat
```

After successful startup, the terminal will display something like:

```
Created system API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy the generated API Key**, edit the `.env` file:

```env
SYSTEM_API_KEY=your_copied_api_key
```

---

## 4. Configure Other Required Parameters

Edit the `.env` file and configure the following parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | `your_password` |
| `BACKEND_PUBLIC_URL` | Backend server public address | `http://your-server-ip:5000` |

**Example Configuration:**

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourSecurePassword123
BACKEND_PUBLIC_URL=http://192.168.1.100:5000
```

---

## 5. Start the Server

After completing all the above configurations, run:

```bash
.\start.bat
```

The system will start normally, and you can access the frontend to begin using it.

---

## Configuration Checklist

After completing deployment, your `.env` file should contain:

```env
# Database Configuration
DB_TYPE=sqlite  # or mysql
DATABASE_URI=   # Required for MySQL

# Admin Account
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password

# Backend URL
BACKEND_PUBLIC_URL=http://your_server_ip:5000

# System API Key
SYSTEM_API_KEY=your_generated_api_key
```

---

## FAQ

### Q: How to change the port number?

A: Edit the `.env` file, add or modify the `SERVER_PORT` parameter:

```env
SERVER_PORT=8080
```

### Q: How to enable debug mode?

A: Edit `start.bat`, change `debug=False` to `debug=True`:

```bash
python app.py --debug
```

### Q: How to view database contents?

A: Use SQLite command line tool:

```bash
sqlite3 app_backend/instance/dota_auto_eval.db
```

---

For questions, please refer to the project documentation or submit an Issue.
