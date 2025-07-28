#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
모든 사용자의 잔액을 올바르게 수정하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_all_balances():
    """모든 사용자의 잔액을 올바르게 수정합니다."""
    
    with app.app_context():
        print("=== 모든 사용자 잔액 수정 ===")
        
        # 모든 사용자 조회 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        total_fixed = 0
        
        for user in users:
            print(f"\n=== {user.username} ({user.role}) ===")
            
            # 해당 사용자의 수수료 로그 조회 (시간순 정렬)
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                continue
            
            print(f"  수수료 로그: {len(fee_logs)}개")
            
            # 잔액 재계산
            current_balance = 0
            fixed_count = 0
            
            for i, log in enumerate(fee_logs):
                # 예상 잔액 계산
                if log.type == '입금':
                    current_balance += log.amount
                elif log.type == '출금':
                    current_balance -= abs(log.amount)
                
                # 잔액이 다르면 수정
                if log.balance != current_balance:
                    old_balance = log.balance
                    log.balance = current_balance
                    fixed_count += 1
                    
                    print(f"    {i+1:2d}. {log.timestamp.strftime('%Y-%m-%d %H:%M')} {log.type} {log.amount:>8,}원")
                    print(f"        잔액: {old_balance:>8,}원 → {current_balance:>8,}원 (차이: {current_balance - old_balance:>8,}원)")
            
            if fixed_count > 0:
                print(f"  ✅ {fixed_count}개의 잔액 수정 완료")
                total_fixed += fixed_count
            else:
                print("  ✅ 잔액이 모두 정확합니다")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ 총 {total_fixed}개의 잔액 수정 완료!")
        
        # 수정 후 검증
        print(f"\n=== 수정 후 검증 ===")
        for user in users:
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            if fee_logs:
                expected_balance = 0
                has_error = False
                
                for log in fee_logs:
                    if log.type == '입금':
                        expected_balance += log.amount
                    elif log.type == '출금':
                        expected_balance -= abs(log.amount)
                    
                    if log.balance != expected_balance:
                        has_error = True
                        break
                
                if has_error:
                    print(f"❌ {user.username}: 아직 잔액 오류가 있습니다")
                else:
                    print(f"✅ {user.username}: 모든 잔액이 정확합니다")

if __name__ == '__main__':
    fix_all_balances() 