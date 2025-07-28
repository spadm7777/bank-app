# auth.py (회원 등급 관리 + 삭제 + 회원 생성 포함 전체코드)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('로그인 실패: 사용자 정보가 일치하지 않습니다.')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/manage-users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        new_role = request.form['new_role']
        parent_id = request.form.get('parent_id') or None
        telegram_group = request.form.get('telegram_group')
        fee_rate = request.form.get('fee_rate')

        user = User.query.get(user_id)
        if user:
            user.role = new_role
            user.parent_id = int(parent_id) if parent_id else None
            user.telegram_group = telegram_group
            user.fee_rate = float(fee_rate)
            db.session.commit()
            flash(f"{user.username} 정보가 수정되었습니다.")
        return redirect(url_for('auth.manage_users'))

    users = User.query.all()
    
    # 각 사용자의 수수료잔액 계산
    from models import FeeLog
    for user in users:
        # 해당 사용자의 수수료 로그에서 잔액 계산
        fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
        balance = 0
        for log in fee_logs:
            if log.type == '입금':
                balance += log.amount
            elif log.type == '출금':
                balance -= abs(log.amount)
        user.fee_balance = balance
    
    return render_template('manage_users.html', users=users)

@auth_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f"{user.username} 계정을 삭제했습니다.")
    else:
        flash('사용자를 찾을 수 없습니다.')

    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자입니다.')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('새 사용자가 등록되었습니다.')
        return redirect(url_for('auth.manage_users'))

    return render_template('register.html')


# --- (아래는 비밀번호 변경 라우트, 기존 코드 유지하며 추가) ---
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form['current_password']
    new_pw = request.form['new_password']
    confirm_pw = request.form['confirm_password']

    if not check_password_hash(current_user.password_hash, current_pw):
        flash('현재 비밀번호가 올바르지 않습니다.')
        return redirect(url_for('index'))

    if new_pw != confirm_pw:
        flash('새 비밀번호가 일치하지 않습니다.')
        return redirect(url_for('index'))

    if len(new_pw) < 4:
        flash('비밀번호는 최소 4자리 이상이어야 합니다.')
        return redirect(url_for('index'))

    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('비밀번호가 성공적으로 변경되었습니다.')
    return redirect(url_for('index'))
# --- (비밀번호 변경 라우트 끝) ---

@auth_bp.route('/manage_fee_balance', methods=['POST'])
@login_required
def manage_fee_balance():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.')
        return redirect(url_for('index'))

    user_id = int(request.form['user_id'])
    operation = request.form['operation']
    amount = int(request.form['amount'])
    note = request.form.get('note', '')

    user = User.query.get(user_id)
    if not user:
        flash('사용자를 찾을 수 없습니다.')
        return redirect(url_for('auth.manage_users'))

    # 수수료 거래내역에 기록
    from models import FeeLog
    from datetime import datetime
    
    # 현재 실제 잔액 계산 (FeeLog 기반)
    fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
    current_balance = 0
    for log in fee_logs:
        if log.type == '입금':
            current_balance += log.amount
        elif log.type == '출금':
            current_balance -= abs(log.amount)
    
    # 수수료잔액 변경
    if operation == 'increase':
        fee_log_type = '입금'
        fee_log_amount = amount
        new_balance = current_balance + amount
    else:  # decrease
        if current_balance < amount:
            flash('잔액이 부족합니다.')
            return redirect(url_for('auth.manage_users'))
        fee_log_type = '출금'
        fee_log_amount = -amount
        new_balance = current_balance - amount

    # FeeLog에 기록
    fee_log = FeeLog(
        user_id=user.id,
        amount=fee_log_amount,
        balance=new_balance,
        timestamp=datetime.now(),
        description=f"관리자 {operation} - {note}" if note else f"관리자 {operation}",
        type=fee_log_type
    )
    
    db.session.add(fee_log)
    
    # User 테이블의 fee_balance도 업데이트 (실제 계산된 값으로)
    user.fee_balance = new_balance
    
    db.session.commit()
    
    operation_text = "증가" if operation == 'increase' else "차감"
    flash(f"{user.username}의 수수료잔액이 {operation_text}되었습니다. (금액: {amount:,}원)")
    
    return redirect(url_for('auth.manage_users'))
