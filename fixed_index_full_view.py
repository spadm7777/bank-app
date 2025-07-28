
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from datetime import datetime, date, timedelta
from db import db
from models import User, Transaction
from auth import auth_bp
from sqlalchemy import inspect, text
from flask_login import LoginManager, current_user, login_required
import io
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.register_blueprint(auth_bp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'telegram_group' not in columns:
        db.session.execute(text('ALTER TABLE users ADD COLUMN telegram_group VARCHAR(100)'))
    if 'fee_rate' not in columns:
        db.session.execute(text('ALTER TABLE users ADD COLUMN fee_rate FLOAT DEFAULT 0.5'))
    db.session.commit()

def get_all_sub_users(user):
    subs = []
    for child in user.children:
        subs.append(child)
        subs.extend(get_all_sub_users(child))
    return subs

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)

@app.route('/')
@login_required
def index():
    user = current_user
    sub_users = [user] + get_all_sub_users(user)
    sub_user_ids = [u.id for u in sub_users]

    try:
        view_user_id = int(request.args.get('user_id', user.id))
    except (TypeError, ValueError):
        view_user_id = user.id

    view_user = User.query.get(view_user_id) if view_user_id in sub_user_ids else None

    transactions = []
    total_deposit = 0
    total_withdraw = 0
    total_fee = 0
    current_balance = 0
    page = int(request.args.get('page', 1))
    page_links = []
    has_prev = has_next = False
    per_page = 1000  # ✅ 더 많이 한 번에 보여줌
    start_date = request.args.get('start_date', date.today().isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    trans_filter = request.args.get('trans_filter', '전체')
    keyword = request.args.get('keyword', '').strip()

    if view_user:
        query = Transaction.query.filter(Transaction.user_id == view_user.id)

        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Transaction.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Transaction.timestamp < end_dt)
        if trans_filter in ['입금', '출금']:
            query = query.filter(Transaction.type == trans_filter)
        if keyword:
            query = query.filter(Transaction.sender.contains(keyword))

        total_count = query.count()
        # ✅ 오래된 순서로 정렬
        transactions = query.order_by(Transaction.timestamp.asc()).all()  # ✅ 모든 거래 출력
        all_transactions = query.order_by(Transaction.timestamp.asc()).all()

        total_deposit = sum(t.amount for t in all_transactions if t.type == '입금')
        total_withdraw = sum(t.amount for t in all_transactions if t.type == '출금')
        total_fee = sum(t.fee for t in all_transactions)
        current_balance = transactions[-1].balance if transactions else 0

        max_page = 1  # ✅ 페이지는 1개로 제한
        page_links = list(range(1, max_page + 1))
        has_prev = False  # ✅ 페이지 이전 없음
        has_next = False  # ✅ 페이지 다음 없음

        if 'download' in request.args:
            output = io.BytesIO()
            df = pd.DataFrame([{
                '시간': t.timestamp, '구분': t.type,
                '금액': t.amount, '잔액': t.balance, '보낸사람': t.sender
            } for t in all_transactions])
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='거래내역')
            output.seek(0)
            return send_file(output, download_name="거래내역.xlsx", as_attachment=True)

    sub_info = []
    for su in sub_users:
        today_tx = Transaction.query.filter(
            Transaction.user_id == su.id,
            Transaction.timestamp >= datetime.combine(date.today(), datetime.min.time()),
            Transaction.timestamp <= datetime.combine(date.today(), datetime.max.time())
        ).all()

        deposit = sum(t.amount for t in today_tx if t.type == '입금')
        withdraw = sum(t.amount for t in today_tx if t.type == '출금')
        fee_rate = su.fee_rate or 0.5
        daily_fee = sum(int(t.amount * fee_rate / 100) for t in today_tx if t.type == '입금')
        all_deposit_tx = Transaction.query.filter(Transaction.user_id == su.id, Transaction.type == '입금').all()
        total_fee_sub = sum(int(t.amount * fee_rate / 100) for t in all_deposit_tx)

        sub_info.append({
            'id': su.id,
            'username': su.username,
            'role': su.role,
            'deposit': deposit,
            'withdraw': withdraw,
            'daily_fee': daily_fee,
            'total_fee': total_fee_sub
        })

    return render_template('index.html',
        sub_users=sub_info,
        transactions=transactions,
        total_deposit=total_deposit,
        total_withdraw=total_withdraw,
        total_fee=total_fee,
        current_balance=current_balance,
        view_username=view_user.username if view_user else '조회불가',
        start_date=start_date,
        end_date=end_date,
        trans_filter=trans_filter,
        page=page,
        page_links=page_links,
        has_prev=has_prev,
        has_next=has_next,
        keyword=keyword,
        fee_rate=view_user.fee_rate if view_user else 0.5
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
