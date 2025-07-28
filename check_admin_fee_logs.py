#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin의 수수료 로그를 상세히 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def check_admin_fee_logs():
    """Admin의 수수료 로그를 상세히 확인합니다."""
    
    with app.app_context():
        print("=== Admin 수수료 로그 상세 확인 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        print(f"Admin ID: {admin.id}")
        
        # 모든 수수료 로그를 시간순으로 조회
        fee_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        if not fee_logs:
            print("수수료 로그가 없습니다.")
            return
        
        print(f"\n총 {len(fee_logs)}개의 수수료 로그:")
        print("-" * 100)
        print(f"{'날짜/시간':<20} {'구분':<10} {'금액':<12} {'잔액':<12} {'설명'}")
        print("-" * 100)
        
        expected_balance = 0
        for i, log in enumerate(fee_logs):
            # 예상 잔액 계산
            if log.type == '입금':
                expected_balance += log.amount
            elif log.type == '출금':
                expected_balance -= abs(log.amount)
            
            # 잔액 오류 확인
            balance_error = ""
            if log.balance != expected_balance:
                balance_error = f" ❌ 오류: 예상 {expected_balance:,}원"
            
            print(f"{log.timestamp.strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{log.type:<10} "
                  f"{log.amount:,}원{'':<8} "
                  f"{log.balance:,}원{'':<8} "
                  f"{log.description}{balance_error}")
        
        print("-" * 100)
        print(f"최종 예상 잔액: {expected_balance:,}원")
        print(f"마지막 로그 잔액: {fee_logs[-1].balance:,}원")
        
        # 2025.07.27 로그 특별 확인
        target_date = datetime(2025, 7, 27, 15, 32)
        target_log = FeeLog.query.filter_by(
            user_id=admin.id, 
            timestamp=target_date
        ).first()
        
        if target_log:
            print(f"\n🔍 2025.07.27 15:32 로그 상세:")
            print(f"  금액: {target_log.amount:,}원")
            print(f"  잔액: {target_log.balance:,}원")
            print(f"  설명: {target_log.description}")
            
            # 이전 로그 확인
            prev_log = FeeLog.query.filter(
                FeeLog.user_id == admin.id,
                FeeLog.timestamp < target_date
            ).order_by(FeeLog.timestamp.desc()).first()
            
            if prev_log:
                print(f"  이전 로그: {prev_log.timestamp.strftime('%Y-%m-%d %H:%M')} - 잔액: {prev_log.balance:,}원")
                expected = prev_log.balance + target_log.amount
                print(f"  예상 잔액: {prev_log.balance:,} + {target_log.amount:,} = {expected:,}원")
                print(f"  실제 잔액: {target_log.balance:,}원")
                if expected != target_log.balance:
                    print(f"  ❌ 잔액 오류: {target_log.balance:,}원 → {expected:,}원")

if __name__ == '__main__':
    check_admin_fee_logs() 