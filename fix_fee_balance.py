#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FeeLog 테이블의 잔액을 올바르게 수정하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_fee_balances():
    """모든 사용자의 FeeLog 잔액을 올바르게 수정합니다."""
    
    with app.app_context():
        print("=== FeeLog 잔액 수정 시작 ===")
        
        # 모든 사용자 조회
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        print(f"총 사용자 수: {len(users)}")
        
        for user in users:
            print(f"\n--- {user.username} ({user.role}) ---")
            
            # 해당 사용자의 모든 FeeLog를 시간순으로 조회
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                continue
            
            print(f"  총 {len(fee_logs)}개의 수수료 로그 발견")
            
            # 올바른 잔액 계산
            current_balance = 0
            updated_count = 0
            
            for log in fee_logs:
                # 이전 잔액과 현재 계산된 잔액 비교
                old_balance = log.balance
                
                # 현재 로그의 금액을 반영하여 잔액 계산
                if log.type == '입금':
                    current_balance += log.amount
                elif log.type == '출금':
                    current_balance -= abs(log.amount)
                
                # 잔액이 다르면 업데이트
                if old_balance != current_balance:
                    log.balance = current_balance
                    updated_count += 1
                    print(f"    {log.timestamp.strftime('%Y-%m-%d %H:%M')}: {old_balance:,}원 → {current_balance:,}원")
            
            if updated_count > 0:
                print(f"  ✅ {updated_count}개의 로그 잔액이 수정되었습니다.")
            else:
                print("  ✅ 모든 잔액이 정확합니다.")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n🎉 모든 사용자의 FeeLog 잔액 수정 완료!")

if __name__ == '__main__':
    fix_fee_balances() 