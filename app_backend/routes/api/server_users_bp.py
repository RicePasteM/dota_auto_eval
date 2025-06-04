from flask import Blueprint, jsonify, request, current_app
from models import db, ServerUser, DotaServer, Email
from utils.auth import auth_required
import threading
import time
import requests
from faker import Faker
import random
import string
import os
from bs4 import BeautifulSoup

server_users_bp = Blueprint('server_users_bp', __name__)

def get_base_url():
    """Get base URL using current app's host and port"""
    host = '127.0.0.1'
    port = current_app.config.get('SERVER_PORT', 5000)
    return f"http://{host}:{port}"

@server_users_bp.route('/server_users', methods=['GET'])
@auth_required()
def get_server_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    server_id = request.args.get('server_id', type=int)
    search = request.args.get('search', '')
    
    # 构建基础查询
    query = ServerUser.query.join(DotaServer).join(Email)
    
    # 添加筛选条件
    if server_id:
        query = query.filter(ServerUser.server_id == server_id)
    if search:
        query = query.filter(
            db.or_(
                ServerUser.username.ilike(f'%{search}%'),
                Email.email.ilike(f'%{search}%')
            )
        )
    
    # 获取分页数据
    pagination = query.paginate(page=page, per_page=per_page)
    
    items = []
    for user in pagination.items:
        items.append({
            'user_id': user.user_id,
            'username': user.username,
            'password': user.password,
            'server_id': user.server_id,
            'server_name': user.dota_server.server_name,
            'email_id': user.email_id,
            'email': user.email.email
        })
    
    return jsonify({
        'items': items,
        'total': pagination.total
    })

@server_users_bp.route('/server_users', methods=['POST'])
@auth_required()
def create_server_user():
    data = request.get_json()
    
    if not all(key in data for key in ['username', 'password', 'server_id', 'email_id']):
        return jsonify({'msg': '缺少必要的字段'}), 400
        
    # 检查服务器和邮箱是否存在
    server = DotaServer.query.get(data['server_id'])
    email = Email.query.get(data['email_id'])
    
    if not server or not email:
        return jsonify({'msg': '服务器或邮箱不存在'}), 404
        
    new_user = ServerUser(
        username=data['username'],
        password=data['password'],
        server_id=data['server_id'],
        email_id=data['email_id']
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'msg': '用户创建成功',
            'user_id': new_user.user_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500

@server_users_bp.route('/server_users/<int:user_id>', methods=['PUT'])
@auth_required()
def update_server_user(user_id):
    user = ServerUser.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'server_id' in data:
        if not DotaServer.query.get(data['server_id']):
            return jsonify({'msg': '服务器不存在'}), 404
        user.server_id = data['server_id']
        
    if 'email_id' in data:
        if not Email.query.get(data['email_id']):
            return jsonify({'msg': '邮箱不存在'}), 404
        user.email_id = data['email_id']
        
    if 'username' in data:
        user.username = data['username']
        
    if 'password' in data:
        user.password = data['password']
    
    try:
        db.session.commit()
        return jsonify({'msg': '用户更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500

@server_users_bp.route('/server_users/<int:user_id>', methods=['DELETE'])
@auth_required()
def delete_server_user(user_id):
    user = ServerUser.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'msg': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 500

# 获取指定服务器下未注册的邮箱
@server_users_bp.route('/server_users/unregistered_emails', methods=['GET'])
@auth_required()
def get_unregistered_emails():
    server_id = request.args.get('server_id', type=int)
    if not server_id:
        return jsonify({'msg': '缺少server_id'}), 400
    registered_email_ids = [eid for (eid,) in ServerUser.query.with_entities(ServerUser.email_id).filter_by(server_id=server_id).all()]
    unregistered_emails = Email.query.filter(~Email.email_id.in_(registered_email_ids)).all()
    return jsonify([{'email_id': e.email_id, 'email': e.email} for e in unregistered_emails])

# 自动注册用户接口
@server_users_bp.route('/server_users/auto_signup', methods=['POST'])
@auth_required()
def auto_signup():
    data = request.get_json()
    server_id = data.get('server_id')
    email_id = data.get('email_id')
    if not server_id or not email_id:
        return jsonify({'msg': '缺少server_id或email_id'}), 400
    server = DotaServer.query.get(server_id)
    email_obj = Email.query.get(email_id)
    if not server or not email_obj:
        return jsonify({'msg': '服务器或邮箱不存在'}), 404
    # 1. 生成用户名和密码
    fake = Faker()
    username = fake.user_name() + ''.join(random.choices(string.digits, k=3))
    password = fake.password(length=random.randint(8, 12), special_chars=False)
    email = email_obj.email
    # 2. 刷新邮箱（假设有get_email_inbox接口）
    try:
        base_url = get_base_url()
        inbox_url = f"{base_url}/manage/emails/{email_id}/inbox"
        requests.get(inbox_url, headers={'Authorization': request.headers.get('Authorization')}, timeout=10)
    except Exception as e:
        return jsonify({'msg': f'刷新邮箱失败: {str(e)}'}), 500
    # 3. 注册逻辑（模拟signup.py）
    try:
        session = requests.Session()
        signup_url = f"{server.server_url}/signup/"
        resp = session.get(signup_url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if not csrf_input:
            return jsonify({'msg': '未找到CSRF令牌'}), 500
        csrf_token = csrf_input.get('value')
        data_post = {
            "username": username,
            "institute": fake.company(),
            "TeamMembers": fake.name(),
            "email": email,
            "password1": password,
            "password2": password,
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {"Referer": signup_url}
        resp2 = session.post(signup_url, data=data_post, headers=headers, timeout=15)
        if "A user with that username already exists" in resp2.text:
            return jsonify({'msg': '用户名已存在', 'username': username, 'email': email, 'password': password, 'result': 'fail'}), 400
        if "confirm your email address to complete the registration" not in resp2.text:
            return jsonify({'msg': '注册请求未成功发出，已删除邮箱', 'result': 'fail', 'debug': resp2.text[:300]}), 500
    except Exception as e:
        return jsonify({'msg': f'注册请求失败: {str(e)}', 'result': 'fail'}), 500
    # 4. 轮询收信，获取激活链接
    activate_url = None
    start_time = time.time()
    max_wait = 60  # 最多等待60秒
    retry = 0
    while time.time() - start_time < max_wait:
        try:
            inbox_resp = requests.get(inbox_url, headers={'Authorization': request.headers.get('Authorization')}, timeout=10)
            inbox_data = inbox_resp.json()
            messages = inbox_data.get('messages', [])
            print(messages)
            for msg in messages:
                if msg['textSubject'] == 'Activate Your DOTA Account':
                    print("收到邮件")
                    # 获取邮件内容
                    msg_id = msg['mid']
                    base_url = get_base_url()
                    msg_url = f"{base_url}/manage/emails/{email_id}/messages/{msg_id}"
                    msg_resp = requests.get(msg_url, headers={'Authorization': request.headers.get('Authorization')}, timeout=10)
                    msg_data = msg_resp.json()
                    body = msg_data.get('body', '')
                    # 查找激活链接
                    import re
                    match = re.search(r'(http[s]?://[^\s]+/activate/[^\s]+)', body)
                    if match:
                        activate_url = match.group(1)
                        break
            if activate_url:
                break
        except Exception as e:
            pass
        time.sleep(15)
    # 5. 激活用户
    if not activate_url:
        return jsonify({'msg': '未收到激活邮件', 'result': 'fail'}), 500
    try:
        act_resp = requests.get(activate_url, timeout=15)
        if act_resp.status_code != 200:
            return jsonify({'msg': '激活链接访问失败', 'result': 'fail', 'activate_url': activate_url}), 500
    except Exception as e:
        return jsonify({'msg': f'激活链接访问异常: {str(e)}', 'result': 'fail', 'activate_url': activate_url}), 500
    # 6. 注册成功，写入ServerUser
    try:
        new_user = ServerUser(
            username=username,
            password=password,
            server_id=server_id,
            email_id=email_id
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg': '注册并激活成功', 'result': 'success', 'username': username, 'password': password, 'email': email})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'写入用户失败: {str(e)}', 'result': 'fail'}), 500 