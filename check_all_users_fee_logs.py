#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
모든 사용자의 수수료 로그 상태를 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def check_all_users_fee_logs():
    """모든 사용자의 수수료 로그 상태를 확인합니다."""
    
    with app.app_context():
        print("=== 모든 사용자 수수료 로그 상태 확인 ===")
        
        # 모든 사용자 조회 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        print(f"총 {len(users)}명의 사용자가 있습니다.")
        print()
        
        for user in users:
            print(f"=== {user.username} ({user.role}) ===")
            
            # 해당 사용자의 수수료 로그 조회
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                print()
                continue
            
            print(f"  수수료 로그: {len(fee_logs)}개")
            
            # 00:00:00으로 설정된 로그들 확인
            zero_time_logs = [log for log in fee_logs if log.timestamp.hour == 0 and log.timestamp.minute == 0 and log.timestamp.second == 0]
            
            print(f"  00:00:00으로 설정된 로그: {len(zero_time_logs)}개")
            
            if zero_time_logs:
                print("  수정이 필요한 로그들:")
                for log in zero_time_logs:
                    print(f"    {log.timestamp.strftime('%Y-%m-%d')} - {log.amount:,}원")
            
            # 잔액 계산 검증
            print("  잔액 계산 검증:")
            expected_balance = 0
            for log in fee_logs:
                if log.type == '입금':
                    expected_balance += log.amount
                elif log.type == '출금':
                    expected_balance -= abs(log.amount)
                
                if log.balance != expected_balance:
                    print(f"    ❌ {log.timestamp.strftime('%Y-%m-%d %H:%M')}: 예상 {expected_balance:,}원 vs 실제 {log.balance:,}원")
                else:
                    print(f"    ✅ {log.timestamp.strftime('%Y-%m-%d %H:%M')}: {log.balance:,}원")
            
            print()

if __name__ == '__main__':
    check_all_users_fee_logs() 