import threading
import time
import os
import random
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from flask import current_app
from models import db, TrainingResult, EvalLog, ServerUser, DotaServer
import json
from sqlalchemy import not_

# Flag to indicate if worker is running
worker_running = False
# 添加全局线程对象来跟踪worker线程
_worker_thread = None

def get_local_base_url():
    """Get base URL using current app's host and port"""
    host = '127.0.0.1'
    port = current_app.config.get('SERVER_PORT', 5000)
    return f"http://{host}:{port}"

def get_system_api_key():
    """Get the system API key for internal requests"""
    return current_app.config.get('SYSTEM_API_KEY')

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
        if not csrf_input:
            return False
        csrf_token = csrf_input.attrs.get('value', '')
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
        if not csrf_input:
            return False, "Failed to get CSRF token"
        csrf_token = csrf_input.attrs.get('value', '')
        if not csrf_token:
            return False, "Failed to get CSRF token value"
        
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
        db.func.count(EvalLog.log_id).label('used_count')
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

def update_progress(training_result, message_type, message_text):
    """Update progress output for a training result"""
    try:
        progress_data = []
        if training_result.progress_output:
            try:
                progress_data = json.loads(training_result.progress_output)
            except:
                progress_data = []
        
        # Add new message
        progress_data.append({
            "type": message_type,
            "message": message_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update database
        training_result.progress_output = json.dumps(progress_data)
        db.session.commit()
    except Exception as e:
        print(f"Error updating progress: {str(e)}")

def process_eval_task(app, training_result_id):
    """Process a single evaluation task for a training result"""
    with app.app_context():
        # Get the training result
        tr = TrainingResult.query.get(training_result_id)
        if not tr or tr.status == "completed":
            return
            
        # Update status to processing
        tr.status = 'processing'
        update_progress(tr, "info", "Starting evaluation process")
        db.session.commit()
        
        try:
            # Get full file path
            temp_dir = os.path.join(app.root_path, "..", 'temp')
            file_path = os.path.join(temp_dir, os.path.basename(tr.submission_file))
            
            if not os.path.exists(file_path):
                tr.status = 'failed'
                tr.eval_result = f"Submission file not found: {tr.submission_file}"
                update_progress(tr, "error", f"Submission file not found: {tr.submission_file}")
                db.session.commit()
                return
                
            # Get available user
            update_progress(tr, "info", "Finding available user account")
            available = get_available_user(tr.training_task.server_id)
            if not available:
                tr.status = 'pending'  # Reset to pending for retry later
                tr.eval_result = "No available accounts at this time"
                update_progress(tr, "warning", "No available accounts at this time, will retry later")
                db.session.commit()
                return
                
            user, limits, used = available
            update_progress(tr, "info", f"Selected account: {user.username}, used {used or 0}/{limits} times today")
            
            # Create evaluation log
            eval_log = EvalLog()
            eval_log.server_id = tr.training_task.server_id
            eval_log.user_id = user.user_id
            eval_log.eval_file_url = tr.submission_file
            eval_log.api_key_id = tr.training_task.api_key_id
            eval_log.training_result_id = tr.result_id
            
            db.session.add(eval_log)
            db.session.commit()
            
            # Submit evaluation
            evaluator = DOTAEvaluator()
            
            # Login
            update_progress(tr, "info", f"Logging in with account {user.username}")
            if not evaluator.login(user.username, user.password):
                eval_log.eval_result = "Login failed"
                tr.status = 'retrying'  # Mark for retry
                update_progress(tr, "error", "Login failed, will retry later")
                db.session.commit()
                return
                
            # Submit evaluation
            update_progress(tr, "info", "Submitting evaluation file")
            success, message = evaluator.submit_evaluation(file_path)
            if not success:
                eval_log.eval_result = f"Evaluation submission failed: {message}"
                tr.status = 'retrying'  # Mark for retry
                update_progress(tr, "error", f"Evaluation submission failed: {message}")
                db.session.commit()
                return
                
            update_progress(tr, "info", "File submitted successfully, waiting for results")
            
            # Wait and check results
            check_count = 0
            start_time = time.time()
            success = False
            
            # Get system API key for internal requests
            system_api_key = get_system_api_key()
            headers = {'X-API-Key': system_api_key}
            
            while time.time() - start_time < 600:  # 10 minutes timeout
                try:
                    check_count += 1
                    update_progress(tr, "info", f"Checking results (attempt {check_count})")
                    
                    # Get inbox content
                    base_url = get_local_base_url()
                    inbox_url = f"{base_url}/api/emails/{user.email_id}/inbox"
                    inbox_resp = requests.get(
                        inbox_url,
                        headers=headers,
                        timeout=10
                    )
                    
                    if inbox_resp.status_code != 200:
                        update_progress(tr, "warning", f"Failed to get inbox: HTTP {inbox_resp.status_code}")
                        time.sleep(10)
                        continue
                        
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
                            
                            if msg_resp.status_code != 200:
                                update_progress(tr, "warning", f"Failed to get message: HTTP {msg_resp.status_code}")
                                continue
                                
                            msg_data = msg_resp.json()
                            result_content = msg_data.get('body', '')
                            
                            # Update evaluation result and training result
                            eval_log.eval_result = result_content
                            tr.eval_result = result_content
                            tr.status = 'completed'
                            tr.completed_at = datetime.now()
                            update_progress(tr, "success", "Evaluation completed successfully")
                            db.session.commit()
                            success = True
                            break
                            
                    if success:
                        break
                        
                except Exception as e:
                    print(f"Error checking results: {str(e)}")
                    update_progress(tr, "warning", f"Error checking results: {str(e)}")
                    
                time.sleep(10)
                
            if not success:
                # Timeout handling - mark for retry
                eval_log.eval_result = "Result wait timeout (10 minutes)"
                tr.status = 'retrying'  # Mark for retry
                update_progress(tr, "error", "Result wait timeout (10 minutes), will retry later")
                db.session.commit()
                
        except Exception as e:
            print(f"Task error: {str(e)}")
            tr.status = 'error'
            tr.eval_result = f"Processing error: {str(e)}"
            update_progress(tr, "error", f"Processing error: {str(e)}")
            db.session.commit()

def task_worker(app):
    """Background worker thread to process tasks"""
    global worker_running
    
    print("#### Task worker started ####")
    
    # Create application context that persists for the thread
    app_context = app.app_context()
    app_context.push()
    
    try:
        # Track when we last checked the database
        last_db_check = 0
        db_check_interval = 30  # Check database every 30 seconds when queue is empty
        
        while worker_running:
            try:
                # Only check database periodically when queue is empty
                current_time = time.time()
                if current_time - last_db_check >= db_check_interval:
                    print("###### Checking database ######")
                    last_db_check = current_time
                    
                    # Check database for any pending tasks
                    # Get tasks marked for retry first
                    task = TrainingResult.query.filter(not_(TrainingResult.status=="completed")).order_by(TrainingResult.submitted_at).first()
                    
                    if task:
                        print(f"###### Processing task {task.result_id} ######")
                        process_eval_task(app, task.result_id)
                        print(f"###### Task {task.result_id} processed ######")
                    
                # Small sleep to prevent CPU hogging
                time.sleep(1)
                
            except Exception as e:
                print(f"Worker error: {str(e)}")
                time.sleep(5)  # Wait a bit on error
    finally:
        # Pop the application context when the worker stops
        app_context.pop()

def start_task_worker(app):
    """Start the background task worker"""
    global worker_running, _worker_thread
    
    # 检查worker是否已经在运行
    if worker_running and _worker_thread and _worker_thread.is_alive():
        print("Worker already running, reusing existing thread")
        return _worker_thread
    
    print("Starting new worker thread")
    worker_running = True
    _worker_thread = threading.Thread(
        target=task_worker,
        args=(app,)
    )
    _worker_thread.daemon = True
    _worker_thread.start()
    
    return _worker_thread  # 返回线程对象以便跟踪

def stop_task_worker():
    """Stop the background task worker"""
    global worker_running
    
    import traceback
    stack = traceback.format_stack()
    print("#### Task worker stopping ####")
    print("Called from:", stack[-2])  # 打印调用栈信息
    
    worker_running = False