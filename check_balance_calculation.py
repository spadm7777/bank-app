#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
잔액 계산식을 정확히 확인하고 문제를 파악하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def check_balance_calculation():
    """잔액 계산식을 정확히 확인하고 문제를 파악합니다."""
    
    with app.app_context():
        print("=== 잔액 계산식 확인 ===")
        
        # 모든 사용자 조회 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        for user in users:
            print(f"\n=== {user.username} ({user.role}) ===")
            
            # 해당 사용자의 수수료 로그 조회 (시간순 정렬)
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                continue
            
            print("날짜/시간                구분         금액           현재잔액         예상잔액         상태")
            print("-" * 120)
            
            expected_balance = 0
            has_error = False
            
            for log in fee_logs:
                timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # 예상 잔액 계산
                if log.type == '입금':
                    expected_balance += log.amount
                elif log.type == '출금':
                    expected_balance -= abs(log.amount)
                
                # 상태 확인
                if log.balance != expected_balance:
                    status = "❌ 오류"
                    has_error = True
                else:
                    status = "✅ 정상"
                
                print(f"{timestamp_str:<20} {log.type:<10} {log.amount:>10,}원 {log.balance:>10,}원 {expected_balance:>10,}원 {status}")
            
            if has_error:
                print(f"  ❌ {user.username}: 잔액 계산 오류가 있습니다!")
            else:
                print(f"  ✅ {user.username}: 모든 잔액이 정확합니다.")

if __name__ == '__main__':
    check_balance_calculation() 