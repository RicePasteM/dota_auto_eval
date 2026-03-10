import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()
    
    if DB_TYPE == 'sqlite':
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'dota_auto_eval.db')
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or f'sqlite:///{db_path}'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'mysql://your_username:your_password@your_host:your_port/dota_auto_eval'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() == 'true'

    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-key-please-change-it' # 强烈建议从环境变量读取或生成一个安全的随机密钥
    JWT_ACCESS_TOKEN_EXPIRES = False # 可以设置为 timedelta 对象, 例如: timedelta(hours=1) 
    
    # 系统内部API调用的密钥
    SYSTEM_API_KEY = os.environ.get('SYSTEM_API_KEY') or secrets.token_hex(32) 