from db import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='가맹점')
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    parent = db.relationship('User', remote_side=[id], backref='children')
    telegram_group = db.Column(db.String(100), nullable=True)
    fee_rate = db.Column(db.Float, nullable=False, default=0.5)
    fee_balance = db.Column(db.Integer, default=0)  # 수수료잔액

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer)
    notification_balance = db.Column(db.Integer, nullable=True)  # 텔레그램에서 파싱한 알림잔액
    sender = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, nullable=False)
    fee = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref='transactions')

class FeeLog(db.Model):
    __tablename__ = 'fee_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=True)       # ✅ 변경: nullable=True
    description = db.Column(db.String(255), nullable=True)  # ✅ 변경: nullable=True
    type = db.Column(db.String(10), nullable=False)

    user = db.relationship('User', backref='fee_logs')

class WithdrawalRequest(db.Model):
    __tablename__ = 'withdrawal_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    current_balance = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='withdrawal_requests')
    processor = db.relationship('User', foreign_keys=[processed_by])
