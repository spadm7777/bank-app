#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수수료 로그 상태 확인 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def check_fee_logs():
    """수수료 로그 상태를 확인합니다."""
    
    with app.app_context():
        print("=== 수수료 로그 상태 확인 ===")
        
        # 모든 사용자 조회
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        print(f"총 사용자 수: {len(users)}")
        
        for user in users:
            print(f"\n--- {user.username} ({user.role}) ---")
            
            # 수수료 로그 개수 확인
            fee_logs = FeeLog.query.filter_by(user_id=user.id).all()
            print(f"수수료 로그 개수: {len(fee_logs)}")
            
            if fee_logs:
                latest_log = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.desc()).first()
                print(f"최근 로그: {latest_log.timestamp.strftime('%Y-%m-%d %H:%M')} - {latest_log.amount:,}원")
            
            # 어제 수수료 계산 테스트
            yesterday = datetime.now() - timedelta(days=1)
            start_dt = datetime(yesterday.year, yesterday.month, yesterday.day)
            end_dt = start_dt + timedelta(days=1)
            
            calculated_fee = compute_downline_fee(user, start_dt, end_dt)
            print(f"어제 계산된 수수료: {calculated_fee:,}원")
            
            # 어제 로그가 있는지 확인
            yesterday_log = FeeLog.query.filter_by(
                user_id=user.id, 
                timestamp=start_dt
            ).first()
            
            if yesterday_log:
                print(f"어제 로그 존재: {yesterday_log.amount:,}원")
            else:
                print("어제 로그 없음")

if __name__ == "__main__":
    check_fee_logs() 