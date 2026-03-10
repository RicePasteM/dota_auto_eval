from flask import Flask, current_app, send_from_directory, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager # Import JWTManager
from models import db # Import db instance
from config import Config # Import configuration
import os
import re
# Import blueprints
from routes.api_bp import api_bp
from utils.task_queue import start_task_worker, stop_task_worker

def get_local_base_url():
    """Get base URL using current app's host and port"""
    with current_app.app_context():
        host = '127.0.0.1'
        port = current_app.config.get('SERVER_PORT', 5000)
        return f"http://{host}:{port}"


def update_backend_url(index_path, backend_url):
    """Update the BASE_URL in index.html using regex pattern matching"""
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match window.BASE_URL assignment in any format
    pattern = r'(window\.BASE_URL\s*=\s*[\'"])(http://[^\'"/]+(?::\d+)?)[\'"]'
    
    if re.search(pattern, content):
        # Replace existing BASE_URL
        new_content = re.sub(pattern, rf'\1{backend_url}"', content)
        
        # Only write if content has changed
        if new_content != content:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    return False

# 在全局范围定义worker线程对象
_worker_thread = None

def check_and_prompt_eula():
    """Check EULA acceptance, prompt user if not accepted"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    eula_file = os.path.join(basedir, 'eula.txt')
    
    # Check if eula.txt exists
    if not os.path.exists(eula_file):
        # Create default eula.txt with False
        with open(eula_file, 'w', encoding='utf-8') as f:
            f.write('False')
        print("\n" + "="*80)
        print("欢迎使用 DOTA Auto Eval 系统 / Welcome to DOTA Auto Eval System")
        print("="*80)
        
        # Print EULA
        from utils.eula import EULA_CONTENT
        print(EULA_CONTENT)
        
        print("="*80)
        print("请查看上面的用户许可协议 (EULA) / Please read the EULA above")
        print(f"如需同意，请在以下文件中将 'False' 改为 'True':")
        print(f"To accept, change 'False' to 'True' in the following file:")
        print(f"  {eula_file}")
        print("="*80 + "\n")
        
        return False
    
    # Check if EULA is accepted
    with open(eula_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if content != 'True':
        print("\n" + "="*80)
        print("错误: 您尚未同意用户许可协议 (EULA) / Error: You have not accepted the EULA")
        print(f"请在以下文件中将内容改为 'True' 以同意协议:")
        print(f"To accept, change the content to 'True' in the following file:")
        print(f"  {eula_file}")
        print("="*80 + "\n")
        return False
    
    return True

def create_app(host='0.0.0.0', port=5000):
    app = Flask(__name__)
    CORS(app)

    # Load configuration from config object
    app.config.from_object(Config)
    
    # Conditionally import pymysql only for MySQL
    if Config.DB_TYPE == 'mysql':
        import pymysql
        pymysql.install_as_MySQLdb()
    
    # Store host and port in app config for other modules to access
    app.config['SERVER_HOST'] = host
    app.config['SERVER_PORT'] = port
    
    # Calculate backend URL
    backend_url = os.environ.get('BACKEND_PUBLIC_URL') or get_local_base_url()
    app.config['BACKEND_URL'] = backend_url

    # Initialize extensions
    db.init_app(app) # Initialize db
    
    # Enable foreign keys for SQLite and create tables if needed
    with app.app_context():
        from sqlalchemy import text
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            db.session.execute(text('PRAGMA foreign_keys = ON'))
        
        # Create tables if they don't exist
        db.create_all()
        
        # Check if this is a new SQLite database (no data)
        from models import DotaServer, ApiKey
        server_count = DotaServer.query.count()
        
        if server_count == 0 and 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            print("Initializing SQLite database with default data...")
            
            # Hardcoded DotaServer data
            default_servers = [
                {'server_name': 'DOTA_1_0_Task1', 'server_url': 'http://bed4rs.net:8001/', 'limits_per_day': 2},
                {'server_name': 'DOTA_2_0_Task1', 'server_url': 'http://bed4rs.net:8005/', 'limits_per_day': 1},
                {'server_name': 'DOTA_1_5_Task1', 'server_url': 'http://bed4rs.net:8002/', 'limits_per_day': 1},
            ]
            
            for server_data in default_servers:
                new_server = DotaServer(**server_data)
                db.session.add(new_server)
            
            db.session.commit()
            print(f"Created {len(default_servers)} default servers")
            
            # Create system API Key
            import secrets
            system_api_key = secrets.token_hex(32)
            new_api_key = ApiKey(
                api_key=system_api_key,
                description='系统API Key',
                is_active=True
            )
            db.session.add(new_api_key)
            db.session.commit()
            
            print(f"Created system API Key: {system_api_key}")
    
    jwt = JWTManager(app) # Initialize JWTManager

    # Frontend static files directory
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manage_frontend', 'dist')
    
    # Update BASE_URL in index.html
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        update_backend_url(index_path, backend_url)
    
    # 在应用启动时只启动一次worker
    with app.app_context():
        global _worker_thread
        _worker_thread = start_task_worker(app)
        print("Worker thread initialized at application startup")
    
    # Register all routes in order of specificity:
    # 1. Static assets route (most specific)
    @app.route('/assets/<path:filename>')
    def serve_static(filename):
        return send_from_directory(os.path.join(frontend_dir, 'assets'), filename)
    
    # 2. API routes (specific prefix)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 3. Root route (exact match)
    @app.route('/')
    def serve_index():
        return send_file(os.path.join(frontend_dir, 'index.html'))
    
    # 4. Catch-all route (least specific)
    @app.route('/<path:path>')
    def catch_all(path):
        # API routes will never reach here because they're handled by the blueprint
        return send_file(os.path.join(frontend_dir, 'index.html'))
    
    # 添加关闭钩子，确保在应用关闭时停止worker
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    return app

if __name__ == '__main__':
    # Check EULA first
    if not check_and_prompt_eula():
        print("程序退出。请同意 EULA 后重新启动。")
        print("Program exits. Please accept EULA and restart.")
        exit(0)
    
    app = create_app(host='0.0.0.0', port=5000)
    app.run(host=app.config['SERVER_HOST'], 
            port=app.config['SERVER_PORT'], 
            debug=False) 