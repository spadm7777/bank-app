#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin의 모든 수수료 로그 잔액을 처음부터 다시 계산하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def recalculate_all_admin_balances():
    """Admin의 모든 수수료 로그 잔액을 처음부터 다시 계산합니다."""
    
    with app.app_context():
        print("=== Admin 모든 수수료 로그 잔액 재계산 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 모든 수수료 로그를 시간순으로 조회
        fee_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        if not fee_logs:
            print("수수료 로그가 없습니다.")
            return
        
        print(f"총 {len(fee_logs)}개의 수수료 로그 재계산:")
        print("-" * 100)
        print(f"{'날짜/시간':<20} {'구분':<10} {'금액':<12} {'이전잔액':<12} {'새잔액':<12} {'설명'}")
        print("-" * 100)
        
        current_balance = 0
        updated_count = 0
        
        for log in fee_logs:
            old_balance = log.balance
            
            # 현재 로그의 금액을 반영하여 잔액 계산
            if log.type == '입금':
                current_balance += log.amount
            elif log.type == '출금':
                current_balance -= abs(log.amount)
            
            # 잔액 업데이트
            log.balance = current_balance
            
            # 변경사항 표시
            if old_balance != current_balance:
                updated_count += 1
                print(f"{log.timestamp.strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{log.type:<10} "
                      f"{log.amount:,}원{'':<8} "
                      f"{old_balance:,}원{'':<8} "
                      f"{current_balance:,}원{'':<8} "
                      f"{log.description[:30]}...")
            else:
                print(f"{log.timestamp.strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{log.type:<10} "
                      f"{log.amount:,}원{'':<8} "
                      f"{old_balance:,}원{'':<8} "
                      f"{current_balance:,}원{'':<8} "
                      f"{log.description[:30]}...")
        
        print("-" * 100)
        print(f"✅ {updated_count}개의 로그 잔액이 수정되었습니다.")
        print(f"최종 잔액: {current_balance:,}원")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n🎉 모든 잔액 재계산 완료!")

if __name__ == '__main__':
    recalculate_all_admin_balances() 