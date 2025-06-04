from flask import Blueprint, jsonify, current_app, request
from flask_jwt_extended import create_access_token
from .api.eval_server_bp import eval_server_bp
from .api.emails_bp import emails_bp
from .api.server_users_bp import server_users_bp
from .api.api_keys_bp import api_keys_bp
from .api.eval_bp import eval_bp
from .api.dashboard_bp import dashboard_bp
from utils.auth import auth_required

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

# 注册服务器管理子蓝图
api_bp.register_blueprint(eval_server_bp)
# 注册邮箱管理子蓝图
api_bp.register_blueprint(emails_bp)
# 注册用户管理子蓝图
api_bp.register_blueprint(server_users_bp)
# 注册API Key管理子蓝图
api_bp.register_blueprint(api_keys_bp)
# 注册验证管理子蓝图
api_bp.register_blueprint(eval_bp)
# 注册仪表盘管理子蓝图
api_bp.register_blueprint(dashboard_bp)

@api_bp.route('/')
@auth_required()
def manage_root():
    return jsonify({'message': 'Welcome to the Management Interface!'})

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    admin_username = current_app.config.get('ADMIN_USERNAME')
    admin_password = current_app.config.get('ADMIN_PASSWORD')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    if username == admin_username and password == admin_password:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401 