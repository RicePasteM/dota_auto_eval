from flask import Blueprint, jsonify, request
from models import db, DotaServer
from utils.auth import auth_required

eval_server_bp = Blueprint('eval_server_bp', __name__)

@eval_server_bp.route('/servers', methods=['GET'])
@auth_required()
def get_servers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取分页数据
    pagination = DotaServer.query.paginate(
        page=page, per_page=per_page, error_out=False)
    
    servers = pagination.items
    
    return jsonify({
        'items': [{
            'server_id': server.server_id,
            'server_name': server.server_name,
            'server_url': server.server_url,
            'limits_per_day': server.limits_per_day
        } for server in servers],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@eval_server_bp.route('/servers', methods=['POST'])
@auth_required()
def create_server():
    data = request.get_json()
    
    if not all(key in data for key in ['server_name', 'server_url', 'limits_per_day']):
        return jsonify({'msg': '缺少必要的字段'}), 400
    
    try:
        new_server = DotaServer(
            server_name=data['server_name'],
            server_url=data['server_url'],
            limits_per_day=data['limits_per_day']
        )
        db.session.add(new_server)
        db.session.commit()
        
        return jsonify({
            'msg': '服务器创建成功',
            'server': {
                'server_id': new_server.server_id,
                'server_name': new_server.server_name,
                'server_url': new_server.server_url,
                'limits_per_day': new_server.limits_per_day
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'创建失败: {str(e)}'}), 500

@eval_server_bp.route('/servers/<int:server_id>', methods=['PUT'])
@auth_required()
def update_server(server_id):
    server = DotaServer.query.get_or_404(server_id)
    data = request.get_json()
    
    try:
        if 'server_name' in data:
            server.server_name = data['server_name']
        if 'server_url' in data:
            server.server_url = data['server_url']
        if 'limits_per_day' in data:
            server.limits_per_day = data['limits_per_day']
            
        db.session.commit()
        return jsonify({
            'msg': '更新成功',
            'server': {
                'server_id': server.server_id,
                'server_name': server.server_name,
                'server_url': server.server_url,
                'limits_per_day': server.limits_per_day
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'更新失败: {str(e)}'}), 500

@eval_server_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@auth_required()
def delete_server(server_id):
    server = DotaServer.query.get_or_404(server_id)
    
    try:
        db.session.delete(server)
        db.session.commit()
        return jsonify({'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'删除失败: {str(e)}'}), 500 