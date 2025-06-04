from flask import Blueprint, jsonify, request
from utils.auth import auth_required
import secrets
from datetime import datetime
from models import db, ApiKey

api_keys_bp = Blueprint('api_keys_bp', __name__)

@api_keys_bp.route('/api-keys', methods=['GET'])
@auth_required()
def list_api_keys():
    try:
        keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
        return jsonify({
            'items': [key.to_dict() for key in keys]
        })
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@api_keys_bp.route('/api-keys', methods=['POST'])
@auth_required()
def create_api_key():
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        # 生成32字节的随机API密钥
        api_key = secrets.token_hex(32)
        
        new_key = ApiKey(
            api_key=api_key,
            description=description
        )
        
        db.session.add(new_key)
        db.session.commit()
        
        return jsonify({
            'api_key': api_key,
            'description': description,
            'key_id': new_key.key_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500

@api_keys_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@auth_required()
def delete_api_key(key_id):
    try:
        key = ApiKey.query.get(key_id)
        if not key:
            return jsonify({'msg': 'API Key不存在'}), 404
            
        db.session.delete(key)
        db.session.commit()
        
        return jsonify({'msg': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500

@api_keys_bp.route('/api-keys/<int:key_id>/toggle', methods=['POST'])
@auth_required()
def toggle_api_key(key_id):
    try:
        key = ApiKey.query.get(key_id)
        if not key:
            return jsonify({'msg': 'API Key不存在'}), 404
            
        key.is_active = not key.is_active
        db.session.commit()
        
        return jsonify({
            'is_active': key.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500 