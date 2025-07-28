#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
7월 27일 수수료를 수동으로 기록하는 테스트 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def test_daily_fee_log():
    """7월 27일 수수료를 수동으로 기록합니다."""
    
    with app.app_context():
        print("=== 7월 27일 수수료 로그 테스트 ===")
        
        # 7월 27일 수수료 기록
        target_date = datetime(2025, 7, 27).date()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        
        print(f"📅 {target_date.strftime('%Y-%m-%d')} 수수료 로그 기록 시작...")
        
        # 모든 사용자 대상 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        for user in users:
            daily_fee = compute_downline_fee(user, start_dt, end_dt)
            if daily_fee == 0:
                continue

            # 동일 날짜의 로그가 존재하는지 확인 (중복 방지)
            existing_log = FeeLog.query.filter_by(user_id=user.id, timestamp=start_dt).first()
            if existing_log:
                print(f"  ⏭️ {user.username}: {target_date.strftime('%Y-%m-%d')} 로그가 이미 존재합니다.")
                continue  # 이미 로그가 존재하면 건너뜁니다.

            # 마지막 수수료 로그에서 잔액 계산
            last_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
            prev_balance = last_log.balance if last_log and last_log.balance is not None else 0
            new_balance = prev_balance + daily_fee

            # 수수료 계산 설명 생성
            description = f"{target_date.strftime('%Y. %m. %d')} 수수료 입금"
            
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
                timestamp=start_dt,
                balance=new_balance,
                description=description,
                type='입금'
            )
            db.session.add(fee_log)
            print(f"  ✅ {user.username}: {daily_fee:,}원 수수료 로그 기록 완료")
        
        db.session.commit()
        print(f"🎉 {target_date.strftime('%Y-%m-%d')} 수수료 로그 기록 완료!")

if __name__ == "__main__":
    test_daily_fee_log() 