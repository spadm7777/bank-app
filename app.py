from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from datetime import datetime, date, timedelta
from db import db
from models import User, Transaction, FeeLog, WithdrawalRequest  # FeeLog 추가
from auth import auth_bp
from routes.admin import admin_bp
from sqlalchemy import inspect, text
from flask_login import LoginManager, current_user, login_required
import io
import pandas as pd
import math
from flask_migrate import Migrate
import schedule
import time
import os
from config import Config


# Flask 애플리케이션 생성
app = Flask(__name__)
app.config.from_object(Config)

migrate = Migrate(app, db)

db.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    # PostgreSQL에서는 컬럼 추가 방식이 다를 수 있으므로 조건부로 처리
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'telegram_group' not in columns:
            db.session.execute(text('ALTER TABLE users ADD COLUMN telegram_group VARCHAR(100)'))
        if 'fee_rate' not in columns:
            db.session.execute(text('ALTER TABLE users ADD COLUMN fee_rate FLOAT DEFAULT 0.5'))
        db.session.commit()

# 수수료 로그 페이지
@app.route('/fee_logs')
@login_required
def fee_logs():
    user_id = current_user.id

    # 검색 파라미터 가져오기
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15  # 한 페이지당 15개
    
    # 기본 쿼리
    query = FeeLog.query.filter_by(user_id=user_id)
    
    # 날짜 필터 적용
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(FeeLog.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(FeeLog.timestamp < end_dt)
        except ValueError:
            pass
    
    # 전체 잔액 계산 (날짜 필터와 관계없이)
    all_logs = FeeLog.query.filter_by(user_id=user_id).order_by(FeeLog.timestamp.asc()).all()
    
    # 잔액 계산
    balance = 0
    for log in all_logs:
        if log.type == '입금':
            balance += log.amount
        elif log.type == '출금':
            balance -= abs(log.amount)  # 출금은 음수이므로 절댓값 사용
    
    # 필터된 로그 수 계산 (페이지네이션용)
    filtered_logs = query.order_by(FeeLog.timestamp.asc()).all()
    
    # 페이지네이션 적용
    pagination = query.order_by(FeeLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 로그가 조회된 경우
    if pagination.items:
        print(f"[LOGGING] {len(pagination.items)} 개의 수수료 로그가 조회되었습니다.")
    
    # 로그가 없다면 알림 메시지 추가
    if not pagination.items:
        flash('수수료 로그가 없습니다.', 'info')
    
    # 수수료 로그 리스트 생성 (페이지네이션된 결과)
    log_list = []
    for log in pagination.items:
        log_list.append({
            'timestamp': log.timestamp.strftime('%Y.%m.%d %H:%M'),
            'type': log.type,
            'amount': log.amount,
            'balance': log.balance,
            'description': log.description or '-'
        })
    
    # 날짜순으로 정렬
    log_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('fee_logs.html', 
                         logs=log_list, 
                         current_balance=balance,
                         pagination=pagination,
                         start_date=start_date,
                         end_date=end_date)

# 출금신청 처리
@app.route('/withdrawal_request', methods=['POST'])
@login_required
def withdrawal_request():
    try:
        amount = int(request.form.get('amount', 0))
        if amount <= 0:
            flash('올바른 금액을 입력해주세요.', 'error')
            return redirect(url_for('fee_logs'))
        
        # 현재 잔액 확인 (마지막 로그의 잔액)
        last_log = FeeLog.query.filter_by(user_id=current_user.id).order_by(FeeLog.timestamp.desc()).first()
        current_balance = last_log.balance if last_log else 0
        
        if amount > current_balance:
            flash('신청 금액이 현재 잔액을 초과합니다.', 'error')
            return redirect(url_for('fee_logs'))
        
        # 출금신청 생성
        withdrawal_req = WithdrawalRequest(
            user_id=current_user.id,
            amount=amount,
            current_balance=current_balance
        )
        db.session.add(withdrawal_req)
        
        # 출금신청 완료 시 즉시 잔액에서 차감
        new_balance = current_balance - amount
        fee_log = FeeLog(
            user_id=current_user.id,
            amount=-amount,
            balance=new_balance,
            timestamp=datetime.now(),
            description=f"{datetime.now().strftime('%Y. %m. %d %H:%M')} 출금신청 {amount:,}원",
            type='출금'
        )
        db.session.add(fee_log)
        
        db.session.commit()
        
        flash('출금신청이 완료되었습니다.', 'success')
        return redirect(url_for('fee_logs'))
        
    except ValueError:
        flash('올바른 금액을 입력해주세요.', 'error')
        return redirect(url_for('fee_logs'))

# 환전신청 관리 페이지
@app.route('/exchange_requests')
@login_required
def exchange_requests():
    if current_user.role != '관리자':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('index'))
    
    # 모든 환전신청 내역 조회 (최근 50개)
    all_requests = WithdrawalRequest.query.order_by(WithdrawalRequest.timestamp.desc()).limit(50).all()
    
    # 처리자 정보 추가
    for req in all_requests:
        if req.processed_by:
            processor = User.query.get(req.processed_by)
            req.processor_name = processor.username if processor else '알 수 없음'
        else:
            req.processor_name = '-'
    
    return render_template('exchange_requests.html', requests=all_requests)

# 출금신청 승인/거절 처리
@app.route('/process_withdrawal/<int:request_id>', methods=['POST'])
@login_required
def process_withdrawal(request_id):
    if current_user.role != '관리자':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('index'))
    
    action = request.form.get('action')
    if action not in ['approve', 'reject']:
        flash('잘못된 요청입니다.', 'error')
        return redirect(url_for('exchange_requests'))
    
    withdrawal_req = WithdrawalRequest.query.get_or_404(request_id)
    if withdrawal_req.status != 'pending':
        flash('이미 처리된 신청입니다.', 'error')
        return redirect(url_for('exchange_requests'))
    
    # 출금신청 처리
    withdrawal_req.status = 'approved' if action == 'approve' else 'rejected'
    withdrawal_req.processed_at = datetime.now()
    withdrawal_req.processed_by = current_user.id
    
    # FeeLog에 처리 기록 추가
    user = User.query.get(withdrawal_req.user_id)
    # 현재 잔액 확인 (마지막 로그의 잔액)
    last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
    prev_balance = last_log.balance if last_log else 0
    
    if action == 'approve':
        # 승인 시 - 이미 출금신청 시 차감되었으므로 추가 차감하지 않음
        fee_log = FeeLog(
            user_id=user.id,
            amount=0,  # 금액 변화 없음
            balance=prev_balance,  # 잔액 유지
            timestamp=datetime.now(),
            description=f"{datetime.now().strftime('%Y. %m. %d %H:%M')} 출금신청 승인 완료",
            type='입금'  # 승인은 긍정적인 처리
        )
        db.session.add(fee_log)
    else:
        # 거절 시 - 출금신청 시 차감된 금액을 다시 복원
        new_balance = prev_balance + withdrawal_req.amount
        fee_log = FeeLog(
            user_id=user.id,
            amount=withdrawal_req.amount,  # 금액 복원
            balance=new_balance,
            timestamp=datetime.now(),
            description=f"{datetime.now().strftime('%Y. %m. %d %H:%M')} 출금신청 거절 - 금액 복원",
            type='입금'
        )
        db.session.add(fee_log)
    
    db.session.commit()
    
    status_text = '승인' if action == 'approve' else '거절'
    flash(f'출금신청이 {status_text}되었습니다.', 'success')
    return redirect(url_for('exchange_requests'))

# 수수료 로그 자동 기록 함수 (매일 00:00에 이전날 수수료 기록)
def record_fee_log():
    # 이전날의 수수료를 기록
    yesterday = datetime.now() - timedelta(days=1)
    start_dt = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_dt = start_dt + timedelta(days=1)

    print(f"📅 {yesterday.strftime('%Y-%m-%d')} 수수료 로그 기록 시작...")

    # 모든 사용자 대상 (매장, 에이전시, 총판, 가맹점, 관리자)
    users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
    
    for user in users:
        daily_fee = compute_downline_fee(user, start_dt, end_dt)
        if daily_fee == 0:
            continue

        # 동일 날짜의 로그가 존재하는지 확인 (중복 방지)
        existing_log = FeeLog.query.filter_by(user_id=user.id, timestamp=start_dt).first()
        if existing_log:
            print(f"  ⏭️ {user.username}: {yesterday.strftime('%Y-%m-%d')} 로그가 이미 존재합니다.")
            continue  # 이미 로그가 존재하면 건너뜁니다.

        # 이전 잔액에서 신규 금액을 더하는 방식으로 잔액 계산
        last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
        prev_balance = last_log.balance if last_log else 0
        new_balance = prev_balance + daily_fee

        # 수수료 계산 설명 생성
        description = f"{start_dt.strftime('%Y. %m. %d')} 수수료 입금"
        
        if user.role == '매장':
            # 매장의 경우 자신의 입금액 정보
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            daily_total = sum(tx.amount for tx in daily_deposits)
            description += f" (자신의 입금액: {daily_total:,}원, 수수료율: {user.fee_rate}%)"
        
        else:
            # 에이전시, 총판, 가맹점, 관리자의 경우 하위 매장 정보
            def get_descendants(u):
                descendants = []
                for child in u.children:
                    descendants.append(child)
                    descendants.extend(get_descendants(child))
                return descendants

            descendants = get_descendants(user)
            store_info = []
            
            for child in descendants:
                if child.role == '매장':
                    daily_deposits = Transaction.query.filter(
                        Transaction.user_id == child.id,
                        Transaction.type == '입금',
                        Transaction.timestamp >= start_dt,
                        Transaction.timestamp < end_dt
                    ).all()
                    daily_total = sum(tx.amount for tx in daily_deposits)
                    if daily_total > 0:
                        store_info.append(f"{child.username}: {daily_total:,}원")

            if store_info:
                description += f" (하위매장: {', '.join(store_info)})"

        fee_log = FeeLog(
            user_id=user.id,
            amount=daily_fee,
            timestamp=datetime.now(),  # 실제 로그가 기록된 시간
            balance=new_balance,
            description=description,
            type='입금'
        )
        db.session.add(fee_log)
        print(f"  ✅ {user.username}: {daily_fee:,}원 수수료 로그 기록 완료 (잔액: {new_balance:,}원)")
    
    db.session.commit()
    print(f"🎉 {yesterday.strftime('%Y-%m-%d')} 수수료 로그 기록 완료!")




# 수동으로 누락된 날짜의 수수료 로그를 기록하는 함수
# 수수료 로그 기록 함수 (누락된 수수료 로그도 기록)
def record_missing_logs():
    # 모든 사용자 대상 (매장, 에이전시, 총판, 가맹점, 관리자)
    users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
    
    for user in users:
        # 날짜별로 FeeLog가 있는지 확인
        logged_dates = {log.timestamp.date() for log in FeeLog.query.filter_by(user_id=user.id).all()}

        # 매장인 경우 자신의 거래 내역을 확인
        if user.role == '매장':
            transactions = Transaction.query.filter_by(user_id=user.id).all()
            print(f"[LOGGING] {user.username} / {len(transactions)}개의 거래 내역을 확인 중...")

            # 중복 날짜 제거
            unique_dates = set()
            for tx in transactions:
                log_date = tx.timestamp.date()
                unique_dates.add(log_date)

            for log_date in unique_dates:
                # 해당 날짜의 로그가 없다면
                if log_date not in logged_dates:
                    start_dt = datetime.combine(log_date, datetime.min.time())
                    end_dt = start_dt + timedelta(days=1)
                    daily_fee = compute_downline_fee(user, start_dt, end_dt)

                    if daily_fee == 0:
                        continue

                    # 로그 추가 과정 확인
                    print(f"[LOGGING] {user.username} / {log_date}에 수수료 {daily_fee} 기록 예정")

                    # 이전 잔액에서 신규 금액을 더하는 방식으로 잔액 계산
                    last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
                    prev_balance = last_log.balance if last_log else 0
                    new_balance = prev_balance + daily_fee

                    # 수수료 계산 설명 생성
                    description = f"{log_date.strftime('%Y. %m. %d')} 수수료 입금"
                    
                    # 매장의 경우 자신의 입금액 정보
                    daily_deposits = Transaction.query.filter(
                        Transaction.user_id == user.id,
                        Transaction.type == '입금',
                        Transaction.timestamp >= start_dt,
                        Transaction.timestamp < end_dt
                    ).all()
                    daily_total = sum(tx.amount for tx in daily_deposits)
                    description += f" (자신의 입금액: {daily_total:,}원, 수수료율: {user.fee_rate}%)"

                    fee_log = FeeLog(
                        user_id=user.id,
                        amount=daily_fee,
                        balance=new_balance,
                        timestamp=datetime.now(),  # 실제 로그가 기록된 시간
                        description=description,
                        type='입금'
                    )
                    db.session.add(fee_log)
                    print(f"[LOGGING] {user.username} / 수수료 로그 추가 완료! (잔액: {new_balance:,}원)")
        
        # 에이전시, 총판, 가맹점, 관리자인 경우 하위 매장의 거래 내역을 확인
        else:
            def get_descendants(u):
                descendants = []
                for child in u.children:
                    descendants.append(child)
                    descendants.extend(get_descendants(child))
                return descendants

            descendants = get_descendants(user)
            store_transactions = []
            
            for child in descendants:
                if child.role == '매장':
                    child_transactions = Transaction.query.filter_by(user_id=child.id).all()
                    store_transactions.extend(child_transactions)
            
            print(f"[LOGGING] {user.username} / 하위 매장 {len(store_transactions)}개의 거래 내역을 확인 중...")
            
            # 중복 날짜 제거
            unique_dates = set()
            for tx in store_transactions:
                log_date = tx.timestamp.date()
                unique_dates.add(log_date)
            
            for log_date in unique_dates:
                # 해당 날짜의 로그가 없다면
                if log_date not in logged_dates:
                    start_dt = datetime.combine(log_date, datetime.min.time())
                    end_dt = start_dt + timedelta(days=1)
                    daily_fee = compute_downline_fee(user, start_dt, end_dt)

                    if daily_fee == 0:
                        continue

                    # 로그 추가 과정 확인
                    print(f"[LOGGING] {user.username} / {log_date}에 수수료 {daily_fee} 기록 예정")

                    # 이전 잔액에서 신규 금액을 더하는 방식으로 잔액 계산
                    last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
                    prev_balance = last_log.balance if last_log else 0
                    new_balance = prev_balance + daily_fee

                    # 수수료 계산 설명 생성
                    description = f"{log_date.strftime('%Y. %m. %d')} 수수료 입금"
                    
                    # 에이전시, 총판, 가맹점, 관리자의 경우 하위 매장 정보
                    def get_descendants(u):
                        descendants = []
                        for child in u.children:
                            descendants.append(child)
                            descendants.extend(get_descendants(child))
                        return descendants

                    descendants = get_descendants(user)
                    store_info = []
                    
                    for child in descendants:
                        if child.role == '매장':
                            daily_deposits = Transaction.query.filter(
                                Transaction.user_id == child.id,
                                Transaction.type == '입금',
                                Transaction.timestamp >= start_dt,
                                Transaction.timestamp < end_dt
                            ).all()
                            daily_total = sum(tx.amount for tx in daily_deposits)
                            if daily_total > 0:
                                store_info.append(f"{child.username}: {daily_total:,}원")

                    if store_info:
                        description += f" (하위매장: {', '.join(store_info)})"

                    fee_log = FeeLog(
                        user_id=user.id,
                        amount=daily_fee,
                        balance=new_balance,
                        timestamp=datetime.now(),  # 실제 로그가 기록된 시간
                        description=description,
                        type='입금'
                    )
                    db.session.add(fee_log)
                    print(f"[LOGGING] {user.username} / 수수료 로그 추가 완료! (잔액: {new_balance:,}원)")

    db.session.commit()
    print("✅ 수수료 로그 기록 완료")


# 이 함수는 수동으로 호출하여 누락된 수수료 로그를 기록할 수 있게 합니다.
@app.route('/record_missing_logs', methods=['GET', 'POST'])
@login_required
def manual_record_logs():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            record_missing_logs()  # 수정된 함수 호출
            flash('모든 사용자에 대한 수수료 로그가 성공적으로 기록되었습니다.', 'success')
        except Exception as e:
            flash(f'오류 발생: {e}', 'danger')

    return render_template('record_missing_logs.html')  # 누락된 수수료 로그 기록 페이지 렌더링

# 수수료 계산 테스트 함수
@app.route('/test_fee_calculation', methods=['GET', 'POST'])
@login_required
def test_fee_calculation_route():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # 어제 날짜로 수수료 계산 테스트
            yesterday = datetime.now() - timedelta(days=1)
            start_dt = datetime(yesterday.year, yesterday.month, yesterday.day)
            end_dt = start_dt + timedelta(days=1)
            
            # 모든 사용자 대상 (매장, 에이전시, 총판, 가맹점, 관리자)
            users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
            
            results = []
            for user in users:
                daily_fee = compute_downline_fee(user, start_dt, end_dt)
                
                # 하위 매장들의 상세 정보 수집
                def get_descendants(u):
                    descendants = []
                    for child in u.children:
                        descendants.append(child)
                        descendants.extend(get_descendants(child))
                    return descendants
                
                descendants = get_descendants(user)
                child_details = []
                
                for child in descendants:
                    if child.role == '매장':
                        daily_deposits = Transaction.query.filter(
                            Transaction.user_id == child.id,
                            Transaction.type == '입금',
                            Transaction.timestamp >= start_dt,
                            Transaction.timestamp < end_dt
                        ).all()
                        daily_total = sum(tx.amount for tx in daily_deposits)
                        if daily_total > 0:
                            child_fee = daily_total * (child.fee_rate or 0) / 100
                            child_details.append({
                                'username': child.username,
                                'role': child.role,
                                'daily_total': daily_total,
                                'fee_rate': child.fee_rate,
                                'child_fee': child_fee
                            })
                
                results.append({
                    'username': user.username,
                    'role': user.role,
                    'fee_rate': user.fee_rate,
                    'daily_fee': daily_fee,
                    'child_details': child_details
                })
            
            flash(f'수수료 계산 테스트 완료. {len(results)}명의 사용자에 대해 계산되었습니다.', 'success')
            return render_template('test_fee_calculation.html', results=results, test_date=yesterday.strftime('%Y-%m-%d'))
            
        except Exception as e:
            flash(f'오류 발생: {e}', 'danger')

    return render_template('test_fee_calculation.html')

# 수수료 로그 기록 함수
# 요구사항에 맞는 수수료 계산 로직
def compute_downline_fee(user, start_dt, end_dt):
    def get_descendants(u):
        descendants = []
        for child in u.children:
            descendants.append(child)
            descendants.extend(get_descendants(child))
        return descendants

    def get_all_stores_in_tree(u):
        """트리 계층의 모든 매장을 찾습니다."""
        stores = []
        for child in get_descendants(u):
            if child.role == '매장':
                stores.append(child)
        return stores

    my_fee = 0

    # 매장인 경우: 자신의 금일 총입금액 × 등록된 요율
    if user.role == '매장':
        daily_deposits = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.type == '입금',
            Transaction.timestamp >= start_dt,
            Transaction.timestamp < end_dt
        ).all()
        daily_total = sum(tx.amount for tx in daily_deposits)
        my_fee = math.floor(daily_total * (user.fee_rate or 0) / 100)
    
    # 에이전시, 총판, 가맹점인 경우: 트리계층의 모든 매장 금일 총입금액 × 자신의 수수료율
    elif user.role in ['에이전시', '총판', '가맹점']:
        stores = get_all_stores_in_tree(user)
        total_daily_deposits = 0
        
        for store in stores:
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            total_daily_deposits += sum(tx.amount for tx in daily_deposits)
        
        my_fee = math.floor(total_daily_deposits * (user.fee_rate or 0) / 100)
    
    # 관리자인 경우: 트리계층의 모든 매장 금일 총입금액 × {매장수수료율 - (에이전시 수수료율 + 총판 수수료율 + 가맹점 수수료율)}
    elif user.role == '관리자':
        stores = get_all_stores_in_tree(user)
        total_fee = 0
        
        for store in stores:
            # 각 매장의 일일 입금액
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            daily_total = sum(tx.amount for tx in daily_deposits)
            
            if daily_total == 0:
                continue
            
            # 매장의 수수료율 (기본값 0.5%)
            store_fee_rate = 0.5
            
            # 해당 매장과 연결된 트리의 에이전시, 총판, 가맹점 수수료율 합계 계산
            total_agent_fee_rate = 0
            
            # 매장에서 관리자까지의 경로를 찾아서 각 등급의 수수료율 합산
            current = store
            while current.parent:
                current = current.parent
                if current.role in ['에이전시', '총판', '가맹점']:
                    total_agent_fee_rate += (current.fee_rate or 0)
            
            # 관리자 수수료율 = 매장수수료율 - (에이전시 + 총판 + 가맹점 수수료율 합계)
            admin_fee_rate = store_fee_rate - total_agent_fee_rate
            
            # 최소 0% 보장
            admin_fee_rate = max(0, admin_fee_rate)
            
            # 해당 매장에 대한 관리자 수수료 계산
            store_admin_fee = math.floor(daily_total * admin_fee_rate / 100)
            total_fee += store_admin_fee
        
        my_fee = total_fee

    return my_fee


def compute_downline_fee_total(user):
    def get_descendants(u):
        descendants = []
        for child in u.children:
            descendants.append(child)
            descendants.extend(get_descendants(child))
        return descendants

    my_fee = 0
    my_id = user.id

    all_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == '입금'
    ).all()
    for tx in all_txs:
        my_fee += math.floor(tx.amount * (user.fee_rate or 0) / 100)

    for child in get_descendants(user):
        if not child.fee_rate:
            continue
        txs = Transaction.query.filter(
            Transaction.user_id == child.id,
            Transaction.type == '입금'
        ).all()
        for tx in txs:
            total_fee = tx.amount * (child.fee_rate or 0) / 100
            current = child
            ancestors = []
            while current.parent:
                current = current.parent
                ancestors.append(current)

            distributed = 0
            for anc in ancestors:
                if anc.id == my_id:
                    if user.username == 'admin':
                        my_fee += math.floor(total_fee - distributed)
                    else:
                        my_fee += math.floor(tx.amount * (user.fee_rate or 0) / 100)
                    break
                else:
                    distributed += tx.amount * (anc.fee_rate or 0) / 100
    return my_fee

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)


def collect_all_ids(user):
    ids = [user.id]
    for child in user.children:
        ids += collect_all_ids(child)
    return ids

def flatten_tree(user, opened_ids, start_dt, end_dt, depth=0):
    rows = []
    def user_info(u, d):
        txs = Transaction.query.filter(
            Transaction.user_id == u.id,
            Transaction.timestamp >= start_dt,
            Transaction.timestamp < end_dt
        ).all()
        deposit = sum(t.amount for t in txs if t.type == '입금')
        withdraw = sum(t.amount for t in txs if t.type == '출금')
        daily_fee = compute_downline_fee(u, start_dt, end_dt)
        total_fee = compute_downline_fee_total(u)
        return {
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'deposit': deposit,
            'withdraw': withdraw,
            'daily_fee': daily_fee,
            'total_fee': total_fee,
            'depth': d
        }
    rows.append(user_info(user, depth))
    if user.id in opened_ids:
        for child in user.children:
            rows.extend(flatten_tree(child, opened_ids, start_dt, end_dt, depth+1))
    return rows


def search_path_tree(target, start_dt, end_dt):
    path = []
    cur = target
    while cur:
        path.append(cur)
        cur = cur.parent
    path = list(reversed(path))  # 루트~타겟
    info_list = []
    for d, u in enumerate(path):
        txs = Transaction.query.filter(
            Transaction.user_id == u.id,
            Transaction.timestamp >= start_dt,
            Transaction.timestamp < end_dt
        ).all()
        deposit = sum(t.amount for t in txs if t.type == '입금')
        withdraw = sum(t.amount for t in txs if t.type == '출금')
        daily_fee = compute_downline_fee(u, start_dt, end_dt)
        total_fee = compute_downline_fee_total(u)
        info_list.append({
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'deposit': deposit,
            'withdraw': withdraw,
            'daily_fee': daily_fee,
            'total_fee': total_fee,
            'depth': d
        })
    for child in target.children:
        txs = Transaction.query.filter(
            Transaction.user_id == child.id,
            Transaction.timestamp >= start_dt,
            Transaction.timestamp < end_dt
        ).all()
        deposit = sum(t.amount for t in txs if t.type == '입금')
        withdraw = sum(t.amount for t in txs if t.type == '출금')
        daily_fee = compute_downline_fee(child, start_dt, end_dt)
        total_fee = compute_downline_fee_total(child)
        info_list.append({
            'id': child.id,
            'username': child.username,
            'role': child.role,
            'deposit': deposit,
            'withdraw': withdraw,
            'daily_fee': daily_fee,
            'total_fee': total_fee,
            'depth': len(path)
        })
    return info_list

@app.route('/')
@login_required
def index():
    user = current_user
    search_user = request.args.get('search_user', '').strip()

    opened = request.args.get('opened', '')
    if opened:
        try:
            opened_ids = set(map(int, filter(None, opened.split(','))))
        except Exception:
            opened_ids = set()
    else:
        opened_ids = set()

    start_date = request.args.get('start_date', date.today().isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    all_tree_ids = collect_all_ids(user)

    if search_user:
        target = User.query.filter(
            (User.username == search_user) | (User.id == (int(search_user) if search_user.isdigit() else -1))
        ).first()
        if not target:
            flash('해당 회원을 찾을 수 없습니다.')
            children_info = flatten_tree(user, set(), start_dt, end_dt)
        else:
            children_info = search_path_tree(target, start_dt, end_dt)
    else:
        children_info = flatten_tree(user, opened_ids, start_dt, end_dt)

    try:
        view_user_id = int(request.args.get('user_id', user.id))
    except (TypeError, ValueError):
        view_user_id = user.id
    view_user = db.session.get(User, view_user_id)
    
    # 에이전시, 총판, 가맹점 등급은 매장의 거래내역을 볼 수 없음
    if view_user and view_user.role == '매장' and user.role in ['에이전시', '총판', '가맹점']:
        # 자신의 하위 매장인지 확인
        def is_descendant(parent, child):
            """parent가 child의 상위 계정인지 확인"""
            current = child
            while current.parent:
                if current.parent.id == parent.id:
                    return True
                current = current.parent
            return False
        
        if not is_descendant(user, view_user):
            flash('매장의 거래내역을 볼 권한이 없습니다.', 'danger')
            view_user = user  # 자신의 거래내역으로 변경
            view_user_id = user.id


    transactions = []
    total_deposit = 0
    total_withdraw = 0
    total_fee = 0
    current_balance = 0
    recent_hour_deposit = 0
    page = int(request.args.get('page', 1))
    page_links = []
    has_prev = has_next = False
    per_page = 20
    trans_filter = request.args.get('trans_filter', '전체')
    keyword = request.args.get('keyword', '').strip()

    # 에이전시, 총판, 가맹점 등급은 거래내역을 볼 수 없음
    if view_user and user.role not in ['에이전시', '총판', '가맹점']:
        query = Transaction.query.filter(Transaction.user_id == view_user.id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_dt)
        if end_date:
            query = query.filter(Transaction.timestamp < end_dt)
        if trans_filter in ['입금', '출금']:
            query = query.filter(Transaction.type == trans_filter)
        if keyword:
            if keyword.isdigit():
                query = query.filter(
                    (Transaction.sender.contains(keyword)) |
                    (Transaction.amount == int(keyword))
                )
            else:
                query = query.filter(Transaction.sender.contains(keyword))

        total_count = query.count()
        max_page = (total_count - 1) // per_page + 1 if total_count > 0 else 1

        # 페이지네이션: 10개만 (예: 1~10, 2~11 등)
        start_p = max(1, page - 5)
        end_p = min(start_p + 9, max_page)
        start_p = max(1, end_p - 9)  # 페이지가 뒤쪽일 때도 10개 유지
        page_links = list(range(start_p, end_p + 1))

        transactions = query.order_by(Transaction.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
        all_transactions = query.all()
        total_deposit = sum(t.amount for t in all_transactions if t.type == '입금')
        total_withdraw = sum(t.amount for t in all_transactions if t.type == '출금')
        
        # 예상잔액 계산을 위해 전체 거래내역을 시간순으로 가져오기 (검색 조건 무관)
        all_transactions_ordered = Transaction.query.filter(
            Transaction.user_id == view_user.id
        ).order_by(Transaction.timestamp.asc()).all()
        
        # 예상잔액 계산: 전체 거래내역을 시간순으로 누적 계산
        expected_balance = 0
        expected_balances = {}  # 각 거래 ID별 예상잔액 저장
        
        for t in all_transactions_ordered:
            if t.type == '입금':
                expected_balance += t.amount
            elif t.type == '출금':
                expected_balance -= abs(t.amount)
            expected_balances[t.id] = expected_balance
        
        # 페이지네이션된 거래들에 예상잔액 추가
        for t in transactions:
            t.expected_balance = expected_balances.get(t.id, 0)

        total_fee = sum(
            math.floor(t.amount * (view_user.fee_rate or 0) / 100)
            for t in Transaction.query.filter(Transaction.user_id == view_user.id, Transaction.type == '입금')
        )

        filtered_fee = sum(
            math.floor(t.amount * (view_user.fee_rate or 0) / 100)
            for t in all_transactions if t.type == '입금'
        )

        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_hour_deposit = sum(
            t.amount for t in all_transactions
            if t.type == '입금' and t.timestamp >= one_hour_ago
        )

        current_balance = transactions[0].balance if transactions else 0
        has_prev = page > 1
        has_next = page < max_page

        if 'download' in request.args:
            output = io.BytesIO()
            df = pd.DataFrame([{
                '시간': t.timestamp, '구분': t.type,
                '금액': t.amount, '예상잔액': expected_balances.get(t.id, 0), 
                '알림잔액': t.notification_balance if t.notification_balance else '-',
                '오차': (expected_balances.get(t.id, 0) - (t.notification_balance or 0)) if t.notification_balance else '-',
                '보낸사람': t.sender
            } for t in all_transactions])
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='거래내역')
            output.seek(0)
            return send_file(output, download_name="거래내역.xlsx", as_attachment=True)
    else:
        filtered_fee = 0
        max_page = 1

    # 대기 중인 환전신청 개수 조회 (admin만)
    pending_requests_count = 0
    if current_user.username == 'admin':
        pending_requests_count = WithdrawalRequest.query.filter_by(status='pending').count()

    return render_template('index.html',
        children_info=children_info,
        transactions=transactions,
        total_deposit=total_deposit,
        total_withdraw=total_withdraw,
        total_fee=filtered_fee if view_user else 0,
        current_balance=current_balance,
        recent_hour_deposit=recent_hour_deposit,
        view_username=view_user.username if view_user else '조회불가',
        start_date=start_date,
        end_date=end_date,
        trans_filter=trans_filter,
        user_id=view_user_id,
        page=page,
        page_links=page_links,
        max_page=max_page,
        has_prev=has_prev,
        has_next=has_next,
        keyword=keyword,
        fee_rate=view_user.fee_rate if view_user else 0.5,
        search_user=search_user,
        opened=opened,
        all_tree_ids=all_tree_ids,  # 전체 펼치기용 id 목록
        pending_requests_count=pending_requests_count
    )

# 환전신청 개수 확인 API
@app.route('/api/pending_requests_count')
@login_required
def get_pending_requests_count():
    if current_user.username == 'admin':
        count = WithdrawalRequest.query.filter_by(status='pending').count()
        return jsonify({'count': count})
    return jsonify({'count': 0})

# 정적 파일 제공 라우트
@app.route('/static/mp3/<filename>')
def serve_mp3(filename):
    return send_from_directory('static/mp3', filename)

# 스케줄러 설정
import schedule
import threading
import time

def run_scheduler():
    """스케줄러를 실행합니다."""
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

def schedule_fee_logging():
    """수수료 로그 기록 스케줄을 설정합니다."""
    # 매일 00:00에 이전날의 수수료 로그 기록
    schedule.every().day.at("00:00").do(record_fee_log)
    print("✅ 수수료 로그 스케줄러가 설정되었습니다. (매일 00:00)")

if __name__ == '__main__':
    # 스케줄러 설정
    schedule_fee_logging()
    
    # 스케줄러를 별도 스레드에서 실행
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    print("🚀 Flask 애플리케이션 시작...")
    print("📅 수수료 로그는 매일 00:00에 자동으로 기록됩니다.")
    
    # 배포 환경에서는 PORT 환경변수 사용
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
