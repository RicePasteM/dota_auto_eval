import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'mysql://your_username:your_password@your_host:your_port/dota_auto_eval'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-key-please-change-it' # 强烈建议从环境变量读取或生成一个安全的随机密钥
    JWT_ACCESS_TOKEN_EXPIRES = False # 可以设置为 timedelta 对象, 例如: timedelta(hours=1) 