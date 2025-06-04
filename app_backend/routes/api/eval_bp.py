from flask import Blueprint, jsonify, request, current_app, Response, stream_with_context, send_file
from flask_jwt_extended import get_jwt_identity
from models import db, ServerUser, DotaServer, Email, EvalLog
import threading
import time
import requests
from datetime import datetime, timedelta
import os
import random
from bs4 import BeautifulSoup
from sqlalchemy import func
import json
import queue
import uuid
from utils.auth import auth_required

def get_local_base_url():
    """Get base URL using current app's host and port"""
    with current_app.app_context():
        host = '127.0.0.1'
        port = current_app.config.get('SERVER_PORT', 5000)
        return f"http://{host}:{port}"


eval_bp = Blueprint('eval_bp', __name__)


# Store active task information
active_tasks = {}

def send_progress(task_id, message):
    """Update task progress information"""
    if task_id in active_tasks:
        active_tasks[task_id]['messages'].append(message)
        active_tasks[task_id]['last_message'] = message

def process_eval_task(app, task_id, server_id, file_path, user_id):
    """Background thread for processing evaluation task"""
    with app.app_context():
        try:
            # Get available user
            headers = {}
            if task_id in active_tasks:
                token = active_tasks[task_id]['token']
                if token:
                    if user_id is None:  # API Key authentication
                        headers['X-API-Key'] = token
                    else:  # JWT authentication
                        headers['Authorization'] = f'Bearer {token}'

            available = get_available_user(server_id)
            if not available:
                send_progress(task_id, {
                    'type': 'error',
                    'message': 'No available accounts'
                })
                return
            
            user, limits, used = available
            send_progress(task_id, {
                'type': 'info',
                'message': f'Selected account: {user.username}, used {used or 0} times today, limit {limits} times'
            })
            
            # Create evaluation log
            eval_log = EvalLog(
                server_id=server_id,
                user_id=user.user_id,
                eval_file_url=active_tasks[task_id]['db_file_path'],
                api_key_id=None
            )
            db.session.add(eval_log)
            db.session.commit()
            
            # Submit evaluation
            evaluator = DOTAEvaluator()
            
            # Login
            send_progress(task_id, {
                'type': 'info',
                'message': f'Logging in account {user.username}...'
            })
            if not evaluator.login(user.username, user.password):
                send_progress(task_id, {
                    'type': 'error',
                    'message': 'Login failed'
                })
                eval_log.eval_result = "Login failed"
                db.session.commit()
                return
            
            # Submit evaluation
            send_progress(task_id, {
                'type': 'info',
                'message': 'Submitting evaluation file...'
            })
            success, message = evaluator.submit_evaluation(file_path)
            if not success:
                send_progress(task_id, {
                    'type': 'error',
                    'message': f'Evaluation submission failed: {message}'
                })
                eval_log.eval_result = f"Evaluation submission failed: {message}"
                db.session.commit()
                return
            
            send_progress(task_id, {
                'type': 'info',
                'message': 'File submitted, waiting for results...'
            })
            
            # Wait and check results
            check_count = 0
            start_time = time.time()
            while time.time() - start_time < 180:  # 3 minutes timeout
                try:
                    check_count += 1
                    send_progress(task_id, {
                        'type': 'info',
                        'message': f'Checking results (attempt {check_count})...'
                    })
                    
                    # Get inbox content
                    base_url = get_local_base_url()
                    inbox_url = f"{base_url}/api/emails/{user.email_id}/inbox"
                    inbox_resp = requests.get(
                        inbox_url, 
                        headers=headers,
                        timeout=10
                    )
                    inbox_data = inbox_resp.json()
                    messages = inbox_data.get('messages', [])
                    
                    for msg in messages:
                        if 'DOTA Evaluation Results' in msg['textSubject']:
                            # Get message content
                            msg_id = msg['mid']
                            msg_url = f"{base_url}/api/emails/{user.email_id}/messages/{msg_id}"
                            msg_resp = requests.get(
                                msg_url,
                                headers=headers,
                                timeout=10
                            )
                            msg_data = msg_resp.json()
                            result_content = msg_data.get('body', '')
                            
                            # Update evaluation result
                            eval_log.eval_result = result_content
                            db.session.commit()
                            
                            send_progress(task_id, {
                                'type': 'success',
                                'message': result_content  # Use email content directly as message
                            })
                            return
                            
                except Exception as e:
                    print(f"Error checking results: {str(e)}")
                    send_progress(task_id, {
                        'type': 'warning',
                        'message': f'Error checking results: {str(e)}'
                    })
                time.sleep(10)
            
            # Timeout handling
            send_progress(task_id, {
                'type': 'error',
                'message': 'Result wait timeout (3 minutes)'
            })
            eval_log.eval_result = "Result wait timeout (3 minutes)"
            db.session.commit()
            
        except Exception as e:
            send_progress(task_id, {
                'type': 'error',
                'message': f'Evaluation process error: {str(e)}'
            })
            print(f"Task error: {str(e)}")
        finally:
            # Set task completion flag
            if task_id in active_tasks:
                active_tasks[task_id]['completed'] = True

class DOTAEvaluator:
    def __init__(self, base_url="http://bed4rs.net:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login(self, username, password):
        """Login to DOTA evaluation system"""
        login_url = f"{self.base_url}/login/"
        response = self.session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token,
            'next': '/evaluation1/'
        }
        headers = {'Referer': login_url}
        response = self.session.post(login_url, data=login_data, headers=headers)
        return "Log in to DOTA" not in response.text
            
    def submit_evaluation(self, zip_file_path, description="Auto evaluation"):
        """Submit evaluation file"""
        if not os.path.exists(zip_file_path):
            return False, "File does not exist"
        submit_url = f"{self.base_url}/evaluation1/"
        response = self.session.get(submit_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
        files = {
            'docfile': (os.path.basename(zip_file_path), open(zip_file_path, 'rb'), 'application/zip')
        }
        data = {
            'csrfmiddlewaretoken': csrf_token,
            'description': description
        }
        headers = {'Referer': submit_url}
        response = self.session.post(submit_url, data=data, files=files, headers=headers)
        success = "You have finished the submit" in response.text
        return success, response.text[:500] if not success else "Submission successful"

def get_available_user(server_id):
    """Get a random user who still has evaluation attempts today"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Query today's used attempts
    used_counts = db.session.query(
        ServerUser.user_id,
        func.count(EvalLog.log_id).label('used_count')
    ).outerjoin(
        EvalLog,
        db.and_(
            EvalLog.user_id == ServerUser.user_id,
            EvalLog.create_time >= today,
            EvalLog.create_time < tomorrow
        )
    ).filter(
        ServerUser.server_id == server_id
    ).group_by(ServerUser.user_id).subquery()
    
    # Find all users with remaining attempts
    available_users = db.session.query(
        ServerUser, DotaServer.limits_per_day, used_counts.c.used_count
    ).join(
        DotaServer
    ).outerjoin(
        used_counts,
        used_counts.c.user_id == ServerUser.user_id
    ).filter(
        ServerUser.server_id == server_id,
        db.or_(
            used_counts.c.used_count == None,
            used_counts.c.used_count < DotaServer.limits_per_day
        )
    ).all()
    
    # If no available users, return None
    if not available_users:
        return None
        
    # Randomly select a user
    return random.choice(available_users)

def get_remaining_counts(server_id):
    """Get total remaining evaluation attempts for all users on this server"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Query today's used attempts and total limits
    result = db.session.query(
        func.sum(DotaServer.limits_per_day).label('total_limits'),
        func.count(EvalLog.log_id).label('total_used')
    ).join(
        ServerUser, ServerUser.server_id == DotaServer.server_id
    ).outerjoin(
        EvalLog,
        db.and_(
            EvalLog.user_id == ServerUser.user_id,
            EvalLog.create_time >= today,
            EvalLog.create_time < tomorrow
        )
    ).filter(
        ServerUser.server_id == server_id
    ).first()
    
    total_limits = result.total_limits or 0
    total_used = result.total_used or 0
    remaining = total_limits - total_used
    
    return remaining

def generate_unique_filename(original_filename):
    """Generate unique filename: timestamp_random_originalname"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_num = str(random.randint(1000, 9999))
    file_ext = os.path.splitext(original_filename)[1]
    return f"{timestamp}_{random_num}{file_ext}"

def ensure_temp_dir():
    """Ensure temp directory exists"""
    temp_dir = os.path.join(current_app.root_path, "..", 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

@eval_bp.route('/eval/submit', methods=['POST'])
@auth_required()
def submit_eval():
    try:
        # Try to get JWT identity, if failed check API Key
        try:
            user_id = get_jwt_identity()
            auth_token = request.headers.get('Authorization', '').split(' ')[1]
        except:
            # If API Key authentication, set user_id to None
            api_key = request.headers.get('X-API-Key')
            if api_key:
                user_id = None
                auth_token = api_key
            else:
                return jsonify({'msg': 'Authentication failed'}), 401

        server_id = request.form.get('server_id', type=int)
        if not server_id:
            return jsonify({'msg': 'Missing server_id'}), 400
        
        if 'eval_file' not in request.files:
            return jsonify({'msg': 'Missing evaluation file'}), 400
            
        eval_file = request.files['eval_file']
        
        # Generate task ID and save file
        task_id = str(uuid.uuid4())
        unique_filename = generate_unique_filename(eval_file.filename)
        temp_dir = ensure_temp_dir()
        file_path = os.path.join(temp_dir, unique_filename)
        eval_file.save(file_path)
        
        # 只保存文件名到数据库
        db_file_path = unique_filename
        
        # Initialize task information
        active_tasks[task_id] = {
            'user_id': user_id,
            'server_id': server_id,
            'file_path': file_path,
            'db_file_path': db_file_path,  # 添加数据库路径
            'token': auth_token,
            'messages': [],
            'last_message': None,
            'completed': False,
            'create_time': datetime.now()
        }
        
        # Start background processing thread
        thread = threading.Thread(
            target=process_eval_task,
            args=(current_app._get_current_object(), task_id, server_id, file_path, user_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'msg': 'Task submitted',
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({'msg': f'Task submission failed: {str(e)}'}), 500

@eval_bp.route('/eval/task/<task_id>', methods=['GET'])
@auth_required()
def get_task_status(task_id):
    """Get task status"""
    # Try to get JWT identity, if failed check API Key
    try:
        user_id = get_jwt_identity()
    except:
        # If API Key authentication, set user_id to None
        api_key = request.headers.get('X-API-Key')
        if api_key:
            user_id = None
        else:
            return jsonify({'msg': 'Authentication failed'}), 401
    
    # Verify task ownership (for API Key auth, allow access to all tasks)
    if task_id not in active_tasks:
        return jsonify({'msg': 'Task does not exist'}), 404
    
    # For regular users, verify task ownership
    if user_id and active_tasks[task_id]['user_id'] != user_id:
        return jsonify({'msg': 'No permission to access this task'}), 403
    
    task = active_tasks[task_id]
    response = {
        'messages': task['messages'],
        'last_message': task['last_message'],
        'completed': task['completed']
    }
    
    # If task is completed and over 5 minutes old, clean up task information
    if task['completed'] and (datetime.now() - task['create_time']).total_seconds() > 300:
        del active_tasks[task_id]
    
    return jsonify(response)

@eval_bp.route('/eval/logs', methods=['GET'])
@auth_required()
def get_eval_logs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        server_id = request.args.get('server_id', type=int)
        username = request.args.get('username', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build base query
        query = db.session.query(
            EvalLog,
            DotaServer.server_name,
            ServerUser.username
        ).join(
            DotaServer,
            DotaServer.server_id == EvalLog.server_id
        ).join(
            ServerUser,
            ServerUser.user_id == EvalLog.user_id
        )
        
        # Add filter conditions
        if server_id:
            query = query.filter(EvalLog.server_id == server_id)
        if username:
            query = query.filter(ServerUser.username.ilike(f'%{username}%'))
        if start_date:
            query = query.filter(EvalLog.create_time >= start_date)
        if end_date:
            query = query.filter(EvalLog.create_time < end_date)
            
        # Sort by creation time in descending order
        query = query.order_by(EvalLog.create_time.desc())
        
        # Get total count
        total = query.count()
        
        # Get paginated data
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        logs_data = [{
            'log_id': log.EvalLog.log_id,
            'server_id': log.EvalLog.server_id,
            'server_name': log.server_name,
            'user_id': log.EvalLog.user_id,
            'username': log.username,
            'eval_file_url': log.EvalLog.eval_file_url,
            'eval_result': log.EvalLog.eval_result,
            'create_time': log.EvalLog.create_time.isoformat()
        } for log in logs]
        
        return jsonify({
            'logs': logs_data,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'msg': f'Failed to get logs: {str(e)}'}), 500

@eval_bp.route('/eval/remaining_counts/<int:server_id>', methods=['GET'])
@auth_required()
def get_server_remaining_counts(server_id):
    """Get remaining evaluation attempts for specified server"""
    try:
        remaining = get_remaining_counts(server_id)
        return jsonify({
            'remaining_counts': remaining
        })
    except Exception as e:
        return jsonify({'msg': f'Failed to get remaining counts: {str(e)}'}), 500

@eval_bp.route('/eval/download/<int:log_id>', methods=['GET'])
@auth_required()
def download_eval_file(log_id):
    """下载评估文件"""
    try:
        # 获取日志记录
        eval_log = EvalLog.query.get_or_404(log_id)
        
        if not eval_log.eval_file_url:
            return jsonify({'msg': '评估文件不存在'}), 404
            
        try:
            # 规范化文件路径
            file_path = os.path.normpath(os.path.join(current_app.root_path, '..', 'temp', os.path.basename(eval_log.eval_file_url)))
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return jsonify({'msg': '评估文件已被删除或移动'}), 404
                
            return send_file(
                file_path,
                as_attachment=True,
                download_name=os.path.basename(file_path)
            )
        except Exception as e:
            print(f"Download error: {str(e)}")
            return jsonify({'msg': '评估文件已被删除或移动'}), 404
            
    except Exception as e:
        return jsonify({'msg': f'下载文件失败: {str(e)}'}), 500 