#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vworld 매장의 2025.07.27 입금액을 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction

def check_vworld_27th_deposits():
    """vworld 매장의 2025.07.27 입금액을 확인합니다."""
    
    with app.app_context():
        print("=== vworld 매장 2025.07.27 입금액 확인 ===")
        
        # vworld 사용자 조회
        vworld = User.query.filter_by(username='vworld').first()
        if not vworld:
            print("❌ vworld 사용자를 찾을 수 없습니다.")
            return
        
        print(f"vworld ID: {vworld.id}")
        
        # 2025.07.27 날짜 범위 설정
        start_dt = datetime(2025, 7, 27, 0, 0)
        end_dt = datetime(2025, 7, 28, 0, 0)
        
        # 2025.07.27 입금 거래 조회
        deposits = Transaction.query.filter(
            Transaction.user_id == vworld.id,
            Transaction.type == '입금',
            Transaction.timestamp >= start_dt,
            Transaction.timestamp < end_dt
        ).order_by(Transaction.timestamp.asc()).all()
        
        print(f"\n2025.07.27 입금 거래 개수: {len(deposits)}")
        
        if deposits:
            print("\n상세 입금 내역:")
            print("-" * 80)
            print(f"{'시간':<20} {'금액':<15} {'보낸사람':<20} {'설명'}")
            print("-" * 80)
            
            total_amount = 0
            for deposit in deposits:
                total_amount += deposit.amount
                print(f"{deposit.timestamp.strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{deposit.amount:,}원{'':<10} "
                      f"{deposit.sender:<20}")
            
            print("-" * 80)
            print(f"총 입금액: {total_amount:,}원")
            
            # 수수료 계산 (0.5%)
            fee_rate = vworld.fee_rate or 0.5
            expected_fee = int(total_amount * fee_rate / 100)
            print(f"수수료율: {fee_rate}%")
            print(f"예상 수수료: {expected_fee:,}원")
            
            # admin이 받아야 할 수수료 계산
            # admin 수수료율 = 매장수수료율(0.5%) - 에이전시/총판/가맹점 수수료율 합계
            print(f"\n=== Admin 수수료 계산 ===")
            
            # vworld에서 admin까지의 경로 찾기
            current = vworld
            path = [current]
            agent_fee_rates = []
            
            while current.parent:
                current = current.parent
                path.append(current)
                if current.role in ['에이전시', '총판', '가맹점']:
                    agent_fee_rates.append((current.username, current.role, current.fee_rate))
            
            print(f"경로: {' → '.join([p.username for p in path])}")
            print(f"에이전시/총판/가맹점: {', '.join([f'{name}({role}: {rate}%)' for name, role, rate in agent_fee_rates])}")
            
            # 에이전시/총판/가맹점 수수료율 합계
            total_agent_fee_rate = sum(rate for _, _, rate in agent_fee_rates)
            print(f"에이전시/총판/가맹점 수수료율 합계: {total_agent_fee_rate}%")
            
            # admin 수수료율 계산
            store_fee_rate = 0.5  # 매장 기본 수수료율
            admin_fee_rate = store_fee_rate - total_agent_fee_rate
            admin_fee_rate = max(0, admin_fee_rate)
            
            print(f"Admin 수수료율: {store_fee_rate}% - {total_agent_fee_rate}% = {admin_fee_rate}%")
            
            # admin이 받아야 할 수수료
            admin_fee = int(total_amount * admin_fee_rate / 100)
            print(f"Admin이 받아야 할 수수료: {admin_fee:,}원")
            
            # 현재 admin 로그와 비교
            from models import FeeLog
            admin = User.query.filter_by(username='admin').first()
            if admin:
                admin_log = FeeLog.query.filter(
                    FeeLog.user_id == admin.id,
                    FeeLog.timestamp >= start_dt,
                    FeeLog.timestamp < end_dt
                ).first()
                
                if admin_log:
                    print(f"\n현재 admin 로그:")
                    print(f"  금액: {admin_log.amount:,}원")
                    print(f"  설명: {admin_log.description}")
                    
                    if admin_log.amount != admin_fee:
                        print(f"❌ 수수료 불일치: 예상 {admin_fee:,}원 vs 실제 {admin_log.amount:,}원")
                    else:
                        print(f"✅ 수수료 일치")
                else:
                    print("❌ admin 2025.07.27 로그가 없습니다.")
        else:
            print("2025.07.27 입금 거래가 없습니다.")

if __name__ == '__main__':
    check_vworld_27th_deposits() 