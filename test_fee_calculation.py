#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수수료 계산 로직 테스트 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def test_fee_calculation():
    """수수료 계산 로직을 테스트합니다."""
    
    with app.app_context():
        print("=== 수수료 계산 로직 테스트 ===")
        
        # 모든 사용자 조회
        users = User.query.all()
        print(f"총 사용자 수: {len(users)}")
        
        # 관리자, 에이전시, 총판, 가맹점 등급 사용자만 필터링
        fee_users = [u for u in users if u.role in ['관리자', '에이전시', '총판', '가맹점']]
        print(f"수수료 계산 대상 사용자 수: {len(fee_users)}")
        
        # 각 사용자별 정보 출력
        for user in fee_users:
            print(f"\n--- {user.username} ({user.role}) ---")
            print(f"수수료율: {user.fee_rate}%")
            
            # 하위 매장들 조회
            def get_descendants(u):
                descendants = []
                for child in u.children:
                    descendants.append(child)
                    descendants.extend(get_descendants(child))
                return descendants
            
            descendants = get_descendants(user)
            print(f"하위 매장 수: {len(descendants)}")
            
            # 하위 매장들의 최근 거래 내역 확인
            yesterday = datetime.now() - timedelta(days=1)
            start_dt = datetime(yesterday.year, yesterday.month, yesterday.day)
            end_dt = start_dt + timedelta(days=1)
            
            total_daily_fee = 0
            for child in descendants:
                if child.fee_rate:
                    # 하위 매장의 일일 총 입금액 계산
                    daily_deposits = Transaction.query.filter(
                        Transaction.user_id == child.id,
                        Transaction.type == '입금',
                        Transaction.timestamp >= start_dt,
                        Transaction.timestamp < end_dt
                    ).all()
                    
                    daily_total = sum(tx.amount for tx in daily_deposits)
                    if daily_total > 0:
                        print(f"  - {child.username}: {daily_total:,}원 (수수료율: {child.fee_rate}%)")
                        total_daily_fee += daily_total
            
            # 수수료 계산
            calculated_fee = compute_downline_fee(user, start_dt, end_dt)
            print(f"계산된 수수료: {calculated_fee:,}원")
            
            # 기존 수수료 로그 확인
            existing_log = FeeLog.query.filter_by(
                user_id=user.id, 
                timestamp=start_dt
            ).first()
            
            if existing_log:
                print(f"기존 로그: {existing_log.amount:,}원 - {existing_log.description}")
            else:
                print("기존 로그: 없음")

if __name__ == "__main__":
    test_fee_calculation() 