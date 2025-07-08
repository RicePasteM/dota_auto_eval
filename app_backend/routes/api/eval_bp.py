from flask import Blueprint, jsonify, request, current_app, Response, stream_with_context, send_file
from flask_jwt_extended import get_jwt_identity
from models import db, ServerUser, DotaServer, Email, EvalLog, TrainingTask, TrainingResult
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
from utils.task_queue import start_task_worker, DOTAEvaluator, get_available_user

def get_local_base_url():
    """Get base URL using current app's host and port"""
    host = '127.0.0.1'
    port = current_app.config.get('SERVER_PORT', 5000)
    return f"http://{host}:{port}"


eval_bp = Blueprint('eval_bp', __name__)


# Store active tasks information
active_tasks = {}

def send_progress(task_id, message):
    """Update task progress information"""
    if task_id in active_tasks:
        active_tasks[task_id]['messages'].append(message)
        active_tasks[task_id]['last_message'] = message

class DOTAEvaluator:
    def __init__(self, base_url="http://bed4rs.net:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login(self, username, password):
        """Login to DOTA evaluation system"""
        login_url = f"{self.base_url}/login/"
        response = self.session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        csrf_token = csrf_input.attrs.get('value') if csrf_input else None
        if not csrf_token:
            return False
        
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
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        csrf_token = csrf_input.attrs.get('value') if csrf_input else None
        if not csrf_token:
            return False, "Failed to get CSRF token"
        
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
    
    # Handle None result
    if not result:
        return 0
        
    # Handle None values
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
            api_key_id = None
        except:
            # If API Key authentication, set user_id to None
            api_key = request.headers.get('X-API-Key')
            if api_key:
                from models import ApiKey
                api_key_obj = ApiKey.query.filter_by(api_key=api_key, is_active=True).first()
                if not api_key_obj:
                    return jsonify({'msg': 'Invalid or inactive API Key'}), 401
                user_id = None
                auth_token = api_key
                api_key_id = api_key_obj.key_id
            else:
                return jsonify({'msg': 'Authentication failed'}), 401

        server_id = request.form.get('server_id', type=int)
        if not server_id:
            return jsonify({'msg': 'Missing server_id'}), 400
        
        if 'eval_file' not in request.files:
            return jsonify({'msg': 'Missing evaluation file'}), 400
            
        eval_file = request.files['eval_file']
        
        # Generate unique filename and save file
        unique_filename = generate_unique_filename(eval_file.filename)
        temp_dir = ensure_temp_dir()
        file_path = os.path.join(temp_dir, unique_filename)
        eval_file.save(file_path)
        
        # 只保存文件名到数据库
        db_file_path = unique_filename
        
        # Check if this is a training-related submission
        training_task_id = request.form.get('training_task_id', type=int)
        epoch = request.form.get('epoch', type=int)
        
        # Always use the background task queue system
        if training_task_id and epoch is not None:
            # Get training task
            training_task = TrainingTask.query.get(training_task_id)
            if not training_task:
                return jsonify({'msg': 'Training task not found'}), 404
                
            if training_task.status != 'active':
                return jsonify({'msg': f'Training task is not active (status: {training_task.status})'}), 400
                
            # Create training result
            result = TrainingResult(
                task_id=training_task_id,
                epoch=epoch,
                submission_file=unique_filename,
                status='pending',
                progress_output=json.dumps([{"type": "info", "message": "Task queued for processing"}])
            )
            
            db.session.add(result)
            db.session.commit()
            
            return jsonify({
                'msg': 'Training epoch submitted for evaluation',
                'result_id': result.result_id
            })
        else:
            # Legacy mode - convert to training task format
            # Create a temporary training task
            temp_task = TrainingTask(
                task_name=f"Manual Evaluation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                description="One-time manual evaluation",
                server_id=server_id,
                api_key_id=api_key_id,
                status='active'
            )
            
            db.session.add(temp_task)
            db.session.commit()
            
            # Create training result
            result = TrainingResult(
                task_id=temp_task.task_id,
                epoch=1,  # Always use epoch 1 for manual evaluations
                submission_file=unique_filename,
                status='pending',
                progress_output=json.dumps([{"type": "info", "message": "Task queued for processing"}])
            )
            
            db.session.add(result)
            db.session.commit()
            
            # Store task info for legacy API compatibility
            task_id = str(uuid.uuid4())
            active_tasks[task_id] = {
                'user_id': user_id,
                'server_id': server_id,
                'file_path': file_path,
                'db_file_path': db_file_path,
                'token': auth_token,
                'messages': [{"type": "info", "message": "Task queued for processing"}],
                'last_message': {"type": "info", "message": "Task queued for processing"},
                'completed': False,
                'create_time': datetime.now(),
                'api_key_id': api_key_id,
                'result_id': result.result_id  # Link to the actual result
            }
            
            return jsonify({
                'msg': 'Task submitted',
                'task_id': task_id,
                'result_id': result.result_id
            })
        
    except Exception as e:
        if 'db' in locals() and db.session.is_active:
            db.session.rollback()
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
    
    # Check if we need to update from the database
    if 'result_id' in task:
        result = TrainingResult.query.get(task['result_id'])
        if result and result.progress_output:
            try:
                progress_messages = json.loads(result.progress_output)
                task['messages'] = progress_messages
                task['last_message'] = progress_messages[-1] if progress_messages else None
                task['completed'] = result.status in ['completed', 'failed', 'error']
            except:
                pass
    
    response = {
        'messages': task['messages'],
        'last_message': task['last_message'],
        'completed': task['completed'],
        'result_id': task.get('result_id')
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
            'create_time': log.EvalLog.create_time.isoformat(),
            'training_result_id': log.EvalLog.training_result_id
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

# =============================================================================
# Training Task Management Endpoints
# =============================================================================

@eval_bp.route('/training', methods=['POST'])
@auth_required()
def create_training_task():
    """Create a new training task"""
    try:
        # Try to get JWT identity, if failed check API Key
        try:
            user_id = get_jwt_identity()
            auth_token = request.headers.get('Authorization', '').split(' ')[1]
            api_key_id = None
        except:
            # If API Key authentication, set user_id to None
            api_key = request.headers.get('X-API-Key')
            if api_key:
                from models import ApiKey
                api_key_obj = ApiKey.query.filter_by(api_key=api_key, is_active=True).first()
                if not api_key_obj:
                    return jsonify({'msg': 'Invalid or inactive API Key'}), 401
                user_id = None
                auth_token = api_key
                api_key_id = api_key_obj.key_id
            else:
                return jsonify({'msg': 'Authentication failed'}), 401
                
        data = request.get_json()
        task_name = data.get('task_name')
        description = data.get('description')
        server_id = data.get('server_id')
        
        if not all([task_name, server_id]):
            return jsonify({'msg': 'Missing required fields'}), 400
            
        # Verify the server exists
        server = DotaServer.query.get(server_id)
        if not server:
            return jsonify({'msg': 'Server not found'}), 404
            
        # Create new training task
        task = TrainingTask(
            task_name=task_name,
            description=description,
            server_id=server_id,
            api_key_id=api_key_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'msg': 'Training task created',
            'task_id': task.task_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Failed to create training task: {str(e)}'}), 500

@eval_bp.route('/training/<int:task_id>/epoch', methods=['POST'])
@auth_required()
def submit_training_epoch(task_id):
    """Submit a training epoch evaluation"""
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
        
        # Get training task
        task = TrainingTask.query.get(task_id)
        if not task:
            return jsonify({'msg': 'Training task not found'}), 404
            
        if task.status != 'active':
            return jsonify({'msg': f'Training task is not active (status: {task.status})'}), 400
            
        # Check if epoch provided
        epoch = request.form.get('epoch', type=int)
        if epoch is None:
            return jsonify({'msg': 'Missing epoch number'}), 400
            
        # Check if file provided
        if 'eval_file' not in request.files:
            return jsonify({'msg': 'Missing evaluation file'}), 400
            
        eval_file = request.files['eval_file']
        
        # Generate unique filename
        unique_filename = generate_unique_filename(eval_file.filename)
        temp_dir = ensure_temp_dir()
        file_path = os.path.join(temp_dir, unique_filename)
        eval_file.save(file_path)
        
        # Create training result
        result = TrainingResult(
            task_id=task_id,
            epoch=epoch,
            submission_file=unique_filename,
            status='pending',
            progress_output=json.dumps([{"type": "info", "message": "Task queued for processing"}])
        )
        
        db.session.add(result)
        db.session.commit()
        
        return jsonify({
            'msg': 'Training epoch submitted for evaluation',
            'result_id': result.result_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Failed to submit epoch: {str(e)}'}), 500

@eval_bp.route('/training', methods=['GET'])
@auth_required()
def list_training_tasks():
    """List all training tasks"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = TrainingTask.query.order_by(TrainingTask.created_at.desc())
        
        # Get total count
        total = query.count()
        
        # Get paginated data
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        tasks_data = [{
            'task_id': task.task_id,
            'task_name': task.task_name,
            'description': task.description,
            'server_id': task.server_id,
            'server_name': task.dota_server.server_name,
            'api_key_id': task.api_key_id,
            'created_at': task.created_at.isoformat(),
            'status': task.status
        } for task in tasks]
        
        return jsonify({
            'tasks': tasks_data,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'msg': f'Failed to get training tasks: {str(e)}'}), 500

@eval_bp.route('/training/<int:task_id>', methods=['GET'])
@auth_required()
def get_training_task(task_id):
    """Get a specific training task with its epochs"""
    try:
        task = TrainingTask.query.get_or_404(task_id)
        
        # Query results
        results = TrainingResult.query.filter_by(task_id=task_id).order_by(TrainingResult.epoch).all()
        
        # Format response
        task_data = {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'description': task.description,
            'server_id': task.server_id,
            'server_name': task.dota_server.server_name,
            'api_key_id': task.api_key_id,
            'created_at': task.created_at.isoformat(),
            'status': task.status,
            'results': [{
                'result_id': result.result_id,
                'epoch': result.epoch,
                'status': result.status,
                'eval_result': result.eval_result if result.status == 'completed' else None,
                'progress_output': json.loads(result.progress_output) if result.progress_output else [],
                'submitted_at': result.submitted_at.isoformat(),
                'completed_at': result.completed_at.isoformat() if result.completed_at else None
            } for result in results]
        }
        
        return jsonify(task_data)
        
    except Exception as e:
        return jsonify({'msg': f'Failed to get training task: {str(e)}'}), 500

@eval_bp.route('/training/result/<int:result_id>', methods=['GET'])
@auth_required()
def get_training_result(result_id):
    """Get details for a specific training result including progress output"""
    try:
        result = TrainingResult.query.get_or_404(result_id)
        
        # Format response
        result_data = {
            'result_id': result.result_id,
            'task_id': result.task_id,
            'epoch': result.epoch,
            'status': result.status,
            'eval_result': result.eval_result,
            'progress_output': json.loads(result.progress_output) if result.progress_output else [],
            'submitted_at': result.submitted_at.isoformat(),
            'completed_at': result.completed_at.isoformat() if result.completed_at else None
        }
        
        return jsonify(result_data)
        
    except Exception as e:
        return jsonify({'msg': f'Failed to get training result: {str(e)}'}), 500

@eval_bp.route('/training/<int:task_id>/results', methods=['GET'])
@auth_required()
def get_training_results(task_id):
    """Get all successful results for a training task"""
    try:
        task = TrainingTask.query.get_or_404(task_id)
        
        # Query successful results
        results = TrainingResult.query.filter_by(
            task_id=task_id,
            status='completed'
        ).order_by(TrainingResult.epoch).all()
        
        # Format response
        results_data = [{
            'result_id': result.result_id,
            'epoch': result.epoch,
            'eval_result': result.eval_result,
            'submitted_at': result.submitted_at.isoformat(),
            'completed_at': result.completed_at.isoformat() if result.completed_at else None
        } for result in results]
        
        return jsonify({
            'task_id': task_id,
            'task_name': task.task_name,
            'results': results_data
        })
        
    except Exception as e:
        return jsonify({'msg': f'Failed to get training results: {str(e)}'}), 500

@eval_bp.route('/training/<int:task_id>/status', methods=['PUT'])
@auth_required()
def update_training_status(task_id):
    """Update training task status (active/inactive)"""
    try:
        task = TrainingTask.query.get_or_404(task_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'msg': 'Missing status field'}), 400
            
        status = data['status']
        if status not in ['active', 'inactive', 'completed']:
            return jsonify({'msg': 'Invalid status value'}), 400
            
        task.status = status
        db.session.commit()
        
        return jsonify({
            'msg': 'Training status updated',
            'task_id': task_id,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Failed to update status: {str(e)}'}), 500 