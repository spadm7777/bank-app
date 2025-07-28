#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수수료 로그 기록 과정 디버깅 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def debug_record_logs():
    """수수료 로그 기록 과정을 디버깅합니다."""
    
    with app.app_context():
        print("=== 수수료 로그 기록 과정 디버깅 ===")
        
        # busan 사용자에 대해 디버깅
        user = User.query.filter_by(username='busan').first()
        if not user:
            print("busan 사용자를 찾을 수 없습니다.")
            return
        
        print(f"사용자: {user.username} ({user.role})")
        
        # 날짜별로 FeeLog가 있는지 확인
        logged_dates = {log.timestamp.date() for log in FeeLog.query.filter_by(user_id=user.id).all()}
        print(f"기존 로그된 날짜: {logged_dates}")
        
        # 하위 매장의 거래 내역 확인
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
                print(f"하위 매장 {child.username}: {len(child_transactions)}개 거래")
        
        print(f"총 하위 매장 거래: {len(store_transactions)}개")
        
        # 중복 날짜 제거
        unique_dates = set()
        for tx in store_transactions:
            log_date = tx.timestamp.date()
            unique_dates.add(log_date)
        
        print(f"고유 날짜: {sorted(unique_dates)}")
        
        # 어제 날짜 확인
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.date()
        print(f"어제 날짜: {yesterday_date}")
        
        if yesterday_date in unique_dates:
            print(f"어제 거래가 있습니다.")
            if yesterday_date not in logged_dates:
                print(f"어제 로그가 없습니다. 수수료 계산 시도...")
                
                start_dt = datetime.combine(yesterday_date, datetime.min.time())
                end_dt = start_dt + timedelta(days=1)
                daily_fee = compute_downline_fee(user, start_dt, end_dt)
                
                print(f"계산된 수수료: {daily_fee:,}원")
                
                if daily_fee > 0:
                    print("수수료 로그를 추가합니다...")
                    
                    # 마지막 수수료 로그에서 잔액 계산
                    last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
                    prev_balance = last_log.balance if last_log and last_log.balance is not None else 0
                    new_balance = prev_balance + daily_fee
                    
                    # 수수료 계산 설명 생성
                    description = f"{yesterday_date.strftime('%Y. %m. %d')} 수수료 입금"
                    
                    # 하위 매장 정보
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
                        timestamp=start_dt,
                        description=description,
                        type='입금'
                    )
                    db.session.add(fee_log)
                    db.session.commit()
                    print("✅ 수수료 로그 추가 완료!")
                else:
                    print("수수료가 0원이므로 로그를 추가하지 않습니다.")
            else:
                print(f"어제 로그가 이미 있습니다.")
        else:
            print(f"어제 거래가 없습니다.")

if __name__ == "__main__":
    debug_record_logs() 