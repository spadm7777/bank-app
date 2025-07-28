#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
admin의 2025.07.27 수수료 로그를 올바른 금액으로 수정하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog

def fix_admin_27th_fee():
    """admin의 2025.07.27 수수료 로그를 올바른 금액으로 수정합니다."""
    
    with app.app_context():
        print("=== admin 2025.07.27 수수료 로그 수정 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 2025.07.27 날짜 범위 설정
        start_dt = datetime(2025, 7, 27, 0, 0)
        end_dt = datetime(2025, 7, 28, 0, 0)
        
        # admin이 관리하는 모든 매장 찾기
        def get_all_stores_in_tree(user):
            """트리 계층의 모든 매장을 찾습니다."""
            stores = []
            for child in user.children:
                if child.role == '매장':
                    stores.append(child)
                else:
                    stores.extend(get_all_stores_in_tree(child))
            return stores
        
        stores = get_all_stores_in_tree(admin)
        print(f"admin이 관리하는 매장 수: {len(stores)}")
        
        # 각 매장의 2025.07.27 입금액 계산
        total_all_deposits = 0
        store_info = []
        
        for store in stores:
            deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            
            store_total = sum(deposit.amount for deposit in deposits)
            total_all_deposits += store_total
            store_info.append(f"{store.username}: {store_total:,}원")
            
            print(f"  {store.username}: {store_total:,}원 ({len(deposits)}건)")
        
        print(f"\n총 입금액: {total_all_deposits:,}원")
        
        # admin이 받아야 할 수수료 계산
        total_admin_fee = 0
        for store in stores:
            deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            
            store_total = sum(deposit.amount for deposit in deposits)
            if store_total == 0:
                continue
            
            # 해당 매장과 연결된 트리의 에이전시, 총판, 가맹점 수수료율 합계 계산
            total_agent_fee_rate = 0
            
            # 매장에서 관리자까지의 경로를 찾아서 각 등급의 수수료율 합산
            current = store
            while current.parent:
                current = current.parent
                if current.role in ['에이전시', '총판', '가맹점']:
                    total_agent_fee_rate += (current.fee_rate or 0)
            
            # 관리자 수수료율 = 매장수수료율 - (에이전시 + 총판 + 가맹점 수수료율 합계)
            store_fee_rate = 0.5  # 매장 기본 수수료율
            admin_fee_rate = store_fee_rate - total_agent_fee_rate
            admin_fee_rate = max(0, admin_fee_rate)
            
            # 해당 매장에 대한 관리자 수수료 계산
            store_admin_fee = int(store_total * admin_fee_rate / 100)
            total_admin_fee += store_admin_fee
        
        print(f"Admin 총 수수료: {total_admin_fee:,}원")
        
        # 현재 admin 로그 찾기
        admin_log = FeeLog.query.filter(
            FeeLog.user_id == admin.id,
            FeeLog.timestamp >= start_dt,
            FeeLog.timestamp < end_dt
        ).first()
        
        if not admin_log:
            print("❌ admin 2025.07.27 로그를 찾을 수 없습니다.")
            return
        
        print(f"\n수정 전:")
        print(f"  금액: {admin_log.amount:,}원")
        print(f"  설명: {admin_log.description}")
        
        # 이전 로그 확인하여 올바른 잔액 계산
        prev_log = FeeLog.query.filter(
            FeeLog.user_id == admin.id,
            FeeLog.timestamp < admin_log.timestamp
        ).order_by(FeeLog.timestamp.desc()).first()
        
        prev_balance = prev_log.balance if prev_log else 0
        new_balance = prev_balance + total_admin_fee
        
        # 수정
        old_amount = admin_log.amount
        old_description = admin_log.description
        
        admin_log.amount = total_admin_fee
        admin_log.balance = new_balance
        admin_log.description = f"2025. 07. 27 수수료 입금 (하위매장: {', '.join(store_info)})"
        
        print(f"\n수정 후:")
        print(f"  금액: {admin_log.amount:,}원")
        print(f"  잔액: {admin_log.balance:,}원")
        print(f"  설명: {admin_log.description}")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ 수정 완료!")
        print(f"  금액: {old_amount:,}원 → {total_admin_fee:,}원")
        print(f"  차이: {total_admin_fee - old_amount:,}원")

if __name__ == '__main__':
    fix_admin_27th_fee() 