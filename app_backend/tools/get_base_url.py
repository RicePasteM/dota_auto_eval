from flask import current_app

def get_local_base_url():
    """Get base URL using current app's host and port"""
    host = '127.0.0.1'
    port = current_app.config.get('SERVER_PORT', 5000)
    return f"http://{host}:{port}"
