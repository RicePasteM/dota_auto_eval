from flask import Blueprint, jsonify, request
from models import db, Email
from utils.auth import auth_required
from tools.smailpro import create_payload, create_email, get_inbox, get_message_content
from datetime import datetime

emails_bp = Blueprint('emails_bp', __name__)

@emails_bp.route('/emails', methods=['GET'])
@auth_required()
def get_emails():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取分页数据
    pagination = Email.query.order_by(Email.email_id.asc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    emails = pagination.items
    
    return jsonify({
        'items': [{
            'email_id': email.email_id,
            'email': email.email
        } for email in emails],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@emails_bp.route('/emails', methods=['POST'])
@auth_required()
def create_email_account():
    try:
        # 获取新的payload
        payload = create_payload(None, url="https://app.sonjj.com/v1/temp_email/create")

        if not payload or not payload.startswith('eyJ'):
            return jsonify({'msg': '获取payload失败', 'detail': payload}), 400
        
        # 使用payload创建邮箱
        email_response = create_email(payload)
        if not email_response.get('email'):
            return jsonify({'msg': '创建邮箱失败', 'detail': email_response}), 400
        
        # 从响应中获取邮箱信息
        email_address = email_response['email']
        
        # 创建新的邮箱记录
        email_record = Email(
            email=email_address,
        )
        
        db.session.add(email_record)
        db.session.commit()
        
        return jsonify({
            'msg': '邮箱创建成功',
            'email': {
                'email_id': email_record.email_id,
                'email': email_record.email,
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '创建失败', 'detail': str(e)}), 500

@emails_bp.route('/emails/<int:email_id>', methods=['DELETE'])
@auth_required()
def delete_email(email_id):
    email = Email.query.get_or_404(email_id)
    
    try:
        db.session.delete(email)
        db.session.commit()
        return jsonify({'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'删除失败: {str(e)}'}), 500


@emails_bp.route('/emails/<int:email_id>/inbox', methods=['GET'])
@auth_required()
def get_email_inbox(email_id):
    email = Email.query.get_or_404(email_id)

    payload = create_payload(email.email, url="https://app.sonjj.com/v1/temp_email/create")
    create_email(payload)

    payload = create_payload(email.email, url="https://app.sonjj.com/v1/temp_email/inbox")
    
    try:
        # 获取收件箱内容
        inbox_response = get_inbox(payload)
        
    
        if 'error' in inbox_response:
            return jsonify({'msg': '获取收件箱失败', 'detail': inbox_response['error']}), 500
            
        return jsonify(inbox_response)
        
    except Exception as e:
        return jsonify({'msg': '获取收件箱失败', 'detail': str(e)}), 500


@emails_bp.route('/emails/<int:email_id>/messages/<message_id>', methods=['GET'])
@auth_required()
def get_email_message(email_id, message_id):
    """获取指定邮件的内容"""
    email = Email.query.get_or_404(email_id)

    payload = create_payload(email.email, url="https://app.sonjj.com/v1/temp_email/message", mid=message_id)
    
    try:
        # 获取邮件内容
        message_response = get_message_content(payload)
        
        if 'error' in message_response:
            return jsonify({'msg': '获取邮件内容失败', 'detail': message_response['error']}), 500
            
        return jsonify(message_response)
        
    except Exception as e:
        return jsonify({'msg': '获取邮件内容失败', 'detail': str(e)}), 500