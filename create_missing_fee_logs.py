#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vworld의 하위 계정들에 대한 누락된 수수료 로그 생성 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def create_missing_fee_logs():
    """vworld의 하위 계정들에 대한 누락된 수수료 로그를 생성합니다."""
    
    with app.app_context():
        print("=== vworld 하위 계정 누락 수수료 로그 생성 ===")
        
        # vworld의 상위 계정들 조회 (sik, busan, admin)
        vworld_user = User.query.filter_by(username='vworld').first()
        if not vworld_user:
            print("vworld 사용자를 찾을 수 없습니다.")
            return
        
        # vworld의 상위 계정들을 찾기 위해 역방향으로 탐색
        def find_ancestors(user):
            ancestors = []
            current = user
            while current.parent:
                ancestors.append(current.parent)
                current = current.parent
            return ancestors
        
        ancestors = find_ancestors(vworld_user)
        print(f"vworld의 상위 계정들: {[ancestor.username for ancestor in ancestors]}")
        
        # 7월 16일부터 27일까지의 날짜 범위
        start_date = datetime(2025, 7, 16).date()
        end_date = datetime(2025, 7, 27).date()
        
        for ancestor in ancestors:
            print(f"\n--- {ancestor.username} ({ancestor.role}) 처리 중 ---")
            
            # 기존 수수료 로그 확인
            existing_logs = FeeLog.query.filter_by(user_id=ancestor.id).all()
            logged_dates = {log.timestamp.date() for log in existing_logs}
            print(f"기존 수수료 로그: {len(existing_logs)}개")
            print(f"기존 로그된 날짜: {sorted(logged_dates)}")
            
            # 누락된 날짜 확인
            missing_dates = []
            current_date = start_date
            while current_date <= end_date:
                if current_date not in logged_dates:
                    missing_dates.append(current_date)
                current_date += timedelta(days=1)
            
            print(f"누락된 날짜: {missing_dates}")
            print(f"누락된 날짜 수: {len(missing_dates)}개")
            
            # 누락된 날짜에 대해 수수료 로그 생성
            for date in missing_dates:
                start_dt = datetime.combine(date, datetime.min.time())
                end_dt = start_dt + timedelta(days=1)
                
                # 수수료 계산
                daily_fee = compute_downline_fee(ancestor, start_dt, end_dt)
                
                if daily_fee > 0:
                    print(f"  {date}: 수수료 {daily_fee:,}원 계산됨")
                    
                    # 마지막 수수료 로그에서 잔액 계산
                    last_log = FeeLog.query.filter_by(user_id=ancestor.id).order_by(FeeLog.timestamp.desc()).first()
                    prev_balance = last_log.balance if last_log and last_log.balance is not None else 0
                    new_balance = prev_balance + daily_fee
                    
                    # 수수료 계산 설명 생성
                    description = f"{date.strftime('%Y. %m. %d')} 수수료 입금"
                    
                    # 하위 매장 정보
                    def get_descendants(u):
                        descendants = []
                        for child in u.children:
                            descendants.append(child)
                            descendants.extend(get_descendants(child))
                        return descendants
                    
                    descendants = get_descendants(ancestor)
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
                        user_id=ancestor.id,
                        amount=daily_fee,
                        balance=new_balance,
                        timestamp=start_dt,
                        description=description,
                        type='입금'
                    )
                    db.session.add(fee_log)
                    print(f"    ✅ 수수료 로그 추가 완료!")
                else:
                    print(f"  {date}: 수수료 0원 (로그 추가 안함)")
            
            # 변경사항 커밋
            db.session.commit()
            print(f"✅ {ancestor.username} 처리 완료")

if __name__ == "__main__":
    create_missing_fee_logs() 