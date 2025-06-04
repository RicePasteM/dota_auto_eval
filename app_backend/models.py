from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class DotaServer(db.Model):
    __tablename__ = 'dota_servers'
    server_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    server_name = db.Column(db.String(50), nullable=False)
    server_url = db.Column(db.String(50), nullable=False)
    limits_per_day = db.Column(db.Integer, nullable=False, default=2)
    eval_logs = db.relationship('EvalLog', backref='dota_server', lazy=True)
    server_users = db.relationship('ServerUser', backref='dota_server', lazy=True)

class Email(db.Model):
    __tablename__ = 'emails'
    email_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), nullable=False)
    server_users = db.relationship('ServerUser', backref='email', lazy=True)

class EvalLog(db.Model):
    __tablename__ = 'eval_logs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    server_id = db.Column(db.Integer, db.ForeignKey('dota_servers.server_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('server_users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.key_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    eval_file_url = db.Column(db.String(255), nullable=False)
    eval_result = db.Column(db.Text, nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class ServerUser(db.Model):
    __tablename__ = 'server_users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    server_id = db.Column(db.Integer, db.ForeignKey('dota_servers.server_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.email_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    eval_logs = db.relationship('EvalLog', backref='server_user', lazy=True)

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    key_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            'key_id': self.key_id,
            'api_key': self.api_key,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_active': self.is_active
        } 