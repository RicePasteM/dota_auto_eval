from flask import Flask, current_app, send_from_directory, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager # Import JWTManager
from models import db # Import db instance
import pymysql
from config import Config # Import configuration
import os
import re
# Import blueprints
from routes.api_bp import api_bp

def get_local_base_url():
    """Get base URL using current app's host and port"""
    with current_app.app_context():
        host = '127.0.0.1'
        port = current_app.config.get('SERVER_PORT', 5000)
        return f"http://{host}:{port}"


pymysql.install_as_MySQLdb()

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

def create_app(host='0.0.0.0', port=5000):
    app = Flask(__name__)
    CORS(app)

    # Load configuration from config object
    app.config.from_object(Config)
    
    # Store host and port in app config for other modules to access
    app.config['SERVER_HOST'] = host
    app.config['SERVER_PORT'] = port
    
    # Calculate backend URL
    backend_url = os.environ.get('BACKEND_PUBLIC_URL') or get_local_base_url()
    app.config['BACKEND_URL'] = backend_url

    # Initialize extensions
    db.init_app(app) # Initialize db
    jwt = JWTManager(app) # Initialize JWTManager

    # Frontend static files directory
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manage_frontend', 'dist')
    
    # Update BASE_URL in index.html
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        update_backend_url(index_path, backend_url)

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
    
    return app

if __name__ == '__main__':
    app = create_app(host='0.0.0.0', port=5000)
    app.run(host=app.config['SERVER_HOST'], 
            port=app.config['SERVER_PORT'], 
            debug=True)