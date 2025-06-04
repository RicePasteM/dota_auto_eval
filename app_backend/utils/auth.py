from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request
from functools import wraps
from datetime import datetime
from models import db, ApiKey

def auth_required():
    """支持JWT和API Key双重认证的装饰器"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 尝试JWT认证
            jwt_auth_failed = True
            try:
                verify_jwt_in_request()
                jwt_auth_failed = False
                return fn(*args, **kwargs)
            except:
                pass
            
            # 如果JWT认证失败，尝试API Key认证
            if jwt_auth_failed:
                api_key = request.headers.get('X-API-Key')
                if not api_key:
                    return jsonify({"msg": "Missing API Key"}), 401
                
                # 验证API Key
                key = ApiKey.query.filter_by(api_key=api_key, is_active=True).first()
                if not key:
                    return jsonify({"msg": "Invalid API Key"}), 401
                
                # 更新最后使用时间
                key.last_used_at = datetime.now()
                db.session.commit()
                
                return fn(*args, **kwargs)
        return decorator
    return wrapper 