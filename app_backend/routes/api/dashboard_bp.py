from flask import Blueprint, jsonify
from models import db, DotaServer, ServerUser, Email, ApiKey, EvalLog
from utils.auth import auth_required
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/stats/overview', methods=['GET'])
@auth_required()
def get_overview_stats():
    """获取系统概览统计数据"""
    try:
        # 获取各种统计数量
        server_count = DotaServer.query.count()
        user_count = ServerUser.query.count()
        email_count = Email.query.count()
        active_api_key_count = ApiKey.query.filter_by(is_active=True).count()
        
        # 获取今日评估次数
        today = datetime.now().date()
        today_eval_count = EvalLog.query.filter(
            func.date(EvalLog.create_time) == today
        ).count()
        
        return jsonify({
            'server_count': server_count,
            'user_count': user_count,
            'email_count': email_count,
            'active_api_key_count': active_api_key_count,
            'today_eval_count': today_eval_count
        })
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/eval_trend', methods=['GET'])
@auth_required()
def get_eval_trend():
    """获取最近7天的评估趋势"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        # 查询每天的评估次数
        daily_stats = db.session.query(
            func.date(EvalLog.create_time).label('date'),
            func.count(EvalLog.log_id).label('count')
        ).filter(
            func.date(EvalLog.create_time) >= start_date,
            func.date(EvalLog.create_time) <= end_date
        ).group_by(
            func.date(EvalLog.create_time)
        ).all()
        
        # 转换为字典格式
        trend_data = {
            str(date): count for date, count in daily_stats
        }
        
        # 补充没有数据的日期
        current_date = start_date
        while current_date <= end_date:
            date_str = str(current_date)
            if date_str not in trend_data:
                trend_data[date_str] = 0
            current_date += timedelta(days=1)
        
        return jsonify(trend_data)
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/server_eval_distribution', methods=['GET'])
@auth_required()
def get_server_eval_distribution():
    """获取各服务器评估分布"""
    try:
        distribution = db.session.query(
            DotaServer.server_name,
            func.count(EvalLog.log_id).label('eval_count')
        ).join(
            EvalLog, EvalLog.server_id == DotaServer.server_id
        ).group_by(
            DotaServer.server_id,
            DotaServer.server_name
        ).all()
        
        return jsonify([{
            'server_name': server_name,
            'eval_count': eval_count
        } for server_name, eval_count in distribution])
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/recent_evals', methods=['GET'])
@auth_required()
def get_recent_evals():
    """获取最近的评估记录"""
    try:
        recent_logs = db.session.query(
            EvalLog,
            DotaServer.server_name,
            ServerUser.username
        ).join(
            DotaServer,
            DotaServer.server_id == EvalLog.server_id
        ).join(
            ServerUser,
            ServerUser.user_id == EvalLog.user_id
        ).order_by(
            EvalLog.create_time.desc()
        ).limit(5).all()
        
        return jsonify([{
            'log_id': log.EvalLog.log_id,
            'server_name': log.server_name,
            'username': log.username,
            'eval_result': log.EvalLog.eval_result,
            'create_time': log.EvalLog.create_time.isoformat()
        } for log in recent_logs])
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/server_remaining', methods=['GET'])
@auth_required()
def get_server_remaining():
    """获取各服务器剩余评估次数"""
    try:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # 获取每个服务器的限制和已使用次数
        server_stats = []
        servers = DotaServer.query.all()
        
        for server in servers:
            # 计算该服务器今日已使用次数
            used_count = EvalLog.query.filter(
                EvalLog.server_id == server.server_id,
                EvalLog.create_time >= today,
                EvalLog.create_time < tomorrow
            ).count()
            
            # 计算总限制次数(服务器限制 * 用户数)
            total_limit = server.limits_per_day * ServerUser.query.filter_by(
                server_id=server.server_id
            ).count()
            
            server_stats.append({
                'server_name': server.server_name,
                'total_limit': total_limit,
                'used_count': used_count,
                'remaining': total_limit - used_count
            })
        
        return jsonify(server_stats)
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/active_users', methods=['GET'])
@auth_required()
def get_active_users():
    """获取最活跃用户TOP5"""
    try:
        # 统计最近30天内评估次数最多的用户
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        active_users = db.session.query(
            ServerUser.username,
            DotaServer.server_name,
            func.count(EvalLog.log_id).label('eval_count')
        ).join(
            EvalLog,
            EvalLog.user_id == ServerUser.user_id
        ).join(
            DotaServer,
            DotaServer.server_id == ServerUser.server_id
        ).filter(
            EvalLog.create_time >= thirty_days_ago
        ).group_by(
            ServerUser.user_id,
            ServerUser.username,
            DotaServer.server_name
        ).order_by(
            func.count(EvalLog.log_id).desc()
        ).limit(5).all()
        
        return jsonify([{
            'username': username,
            'server_name': server_name,
            'eval_count': eval_count
        } for username, server_name, eval_count in active_users])
    except Exception as e:
        return jsonify({'msg': str(e)}), 500

@dashboard_bp.route('/stats/api_usage', methods=['GET'])
@auth_required()
def get_api_usage():
    """获取API使用情况统计"""
    try:
        # 获取API Key总数和活跃数量
        total_keys = ApiKey.query.count()
        active_keys = ApiKey.query.filter_by(is_active=True).count()
        
        # 获取最近的API评估记录
        recent_api_logs = db.session.query(
            EvalLog
        ).filter(
            EvalLog.api_key_id != None
        ).order_by(
            EvalLog.create_time.desc()
        ).limit(5).all()
        
        return jsonify({
            'total_keys': total_keys,
            'active_keys': active_keys,
            'recent_logs': [{
                'log_id': log.log_id,
                'create_time': log.create_time.isoformat(),
                'eval_result': log.eval_result
            } for log in recent_api_logs]
        })
    except Exception as e:
        return jsonify({'msg': str(e)}), 500 