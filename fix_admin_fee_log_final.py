#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin의 2025.07.27 로그를 최종적으로 수정하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_admin_fee_log_final():
    """Admin의 2025.07.27 로그를 최종적으로 수정합니다."""
    
    with app.app_context():
        print("=== Admin 2025.07.27 로그 최종 수정 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 2025.07.27 로그 찾기
        start_date = datetime(2025, 7, 27, 0, 0)
        end_date = datetime(2025, 7, 28, 0, 0)
        
        target_log = FeeLog.query.filter(
            FeeLog.user_id == admin.id,
            FeeLog.timestamp >= start_date,
            FeeLog.timestamp < end_date
        ).first()
        
        if not target_log:
            print("❌ 2025.07.27 로그를 찾을 수 없습니다.")
            return
        
        print(f"수정 전:")
        print(f"  날짜/시간: {target_log.timestamp}")
        print(f"  구분: {target_log.type}")
        print(f"  금액: {target_log.amount:,}원")
        print(f"  잔액: {target_log.balance:,}원")
        print(f"  설명: {target_log.description}")
        
        # 이전 로그 확인
        prev_log = FeeLog.query.filter(
            FeeLog.user_id == admin.id,
            FeeLog.timestamp < target_log.timestamp
        ).order_by(FeeLog.timestamp.desc()).first()
        
        if not prev_log:
            print("❌ 이전 로그를 찾을 수 없습니다.")
            return
        
        print(f"  이전 로그: {prev_log.timestamp.strftime('%Y-%m-%d %H:%M')} - 잔액: {prev_log.balance:,}원")
        
        # 올바른 잔액 계산
        correct_balance = prev_log.balance + target_log.amount
        print(f"  예상 잔액: {prev_log.balance:,} + {target_log.amount:,} = {correct_balance:,}원")
        
        # 수정
        old_balance = target_log.balance
        old_type = target_log.type
        target_log.balance = correct_balance
        target_log.type = '입금'  # 일일수수료 → 입금으로 수정
        target_log.timestamp = datetime(2025, 7, 27, 0, 0)  # 00:00으로 수정
        target_log.description = "2025. 07. 27 수수료 입금 (하위매장: vworld: 115,179,000원)"
        
        print(f"\n수정 후:")
        print(f"  날짜/시간: {target_log.timestamp}")
        print(f"  구분: {target_log.type}")
        print(f"  금액: {target_log.amount:,}원")
        print(f"  잔액: {target_log.balance:,}원")
        print(f"  설명: {target_log.description}")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ 수정 완료!")
        print(f"  잔액: {old_balance:,}원 → {correct_balance:,}원")
        print(f"  구분: {old_type} → 입금")
        print(f"  시간: 00:00:00")

if __name__ == '__main__':
    fix_admin_fee_log_final() 