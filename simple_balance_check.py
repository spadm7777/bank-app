#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
간단하게 잔액 문제를 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def simple_balance_check():
    """간단하게 잔액 문제를 확인합니다."""
    
    with app.app_context():
        print("=== 잔액 문제 확인 ===")
        
        # admin 사용자만 확인
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("admin 사용자를 찾을 수 없습니다.")
            return
        
        # admin의 수수료 로그 조회 (시간순 정렬)
        fee_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        print(f"admin 수수료 로그: {len(fee_logs)}개")
        print()
        
        expected_balance = 0
        errors = []
        
        for i, log in enumerate(fee_logs):
            # 예상 잔액 계산
            if log.type == '입금':
                expected_balance += log.amount
            elif log.type == '출금':
                expected_balance -= abs(log.amount)
            
            # 오류 확인
            if log.balance != expected_balance:
                errors.append({
                    'index': i + 1,
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M'),
                    'type': log.type,
                    'amount': log.amount,
                    'current_balance': log.balance,
                    'expected_balance': expected_balance,
                    'difference': log.balance - expected_balance
                })
        
        if errors:
            print("❌ 잔액 오류 발견:")
            for error in errors:
                print(f"  {error['index']}. {error['timestamp']} ({error['type']} {error['amount']:,}원)")
                print(f"     현재잔액: {error['current_balance']:,}원")
                print(f"     예상잔액: {error['expected_balance']:,}원")
                print(f"     차이: {error['difference']:,}원")
                print()
        else:
            print("✅ 모든 잔액이 정확합니다.")

if __name__ == '__main__':
    simple_balance_check() 