#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
관리자 수수료 계산 디버깅 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import math

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def debug_admin_fee():
    """관리자 수수료 계산을 디버깅합니다."""
    
    with app.app_context():
        print("=== 관리자 수수료 계산 디버깅 ===")
        
        # admin 사용자 조회
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
            
        print(f"\n=== admin 사용자 정보 ===")
        print(f"사용자명: {admin_user.username}")
        print(f"등급: {admin_user.role}")
        print(f"수수료율: {admin_user.fee_rate}%")
        
        # 어제 날짜로 테스트
        yesterday = datetime.now() - timedelta(days=1)
        start_dt = datetime(yesterday.year, yesterday.month, yesterday.day)
        end_dt = start_dt + timedelta(days=1)
        
        print(f"\n=== 테스트 날짜: {start_dt.strftime('%Y-%m-%d')} ===")
        
        # 하위 매장 조회 함수
        def get_descendants(u):
            descendants = []
            for child in u.children:
                descendants.append(child)
                descendants.extend(get_descendants(child))
            return descendants
        
        # admin의 하위 매장들
        admin_descendants = get_descendants(admin_user)
        admin_stores = [child for child in admin_descendants if child.role == '매장']
        admin_agents = [child for child in admin_descendants if child.role in ['에이전시', '총판', '가맹점']]
        
        print(f"\n=== admin의 하위 매장들 ({len(admin_stores)}개) ===")
        total_daily_deposits = 0
        for store in admin_stores:
            print(f"  - {store.username} (등급: {store.role}, 수수료율: {store.fee_rate}%)")
            
            # 하위 매장의 일일 입금액 확인
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            
            daily_total = sum(tx.amount for tx in daily_deposits)
            total_daily_deposits += daily_total
            print(f"    일일 총 입금액: {daily_total:,}원")
        
        print(f"\n=== admin의 하위 에이전시/총판/가맹점들 ({len(admin_agents)}개) ===")
        for agent in admin_agents:
            print(f"  - {agent.username} (등급: {agent.role}, 수수료율: {agent.fee_rate}%)")
        
        print(f"\n=== 매장별 수수료 계산 과정 ===")
        total_fee = 0
        
        for store in admin_stores:
            if store.username == 'aaaa':  # 입금액이 0인 매장은 건너뛰기
                continue
                
            print(f"\n--- {store.username} 매장 ---")
            
            # 해당 매장의 일일 입금액
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == store.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            daily_total = sum(tx.amount for tx in daily_deposits)
            print(f"일일 총 입금액: {daily_total:,}원")
            
            # 매장에서 관리자까지의 경로 찾기
            current = store
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
            
            # 관리자 수수료율 계산
            store_fee_rate = 0.5
            admin_fee_rate = store_fee_rate - total_agent_fee_rate
            admin_fee_rate = max(0, admin_fee_rate)
            
            print(f"관리자 수수료율: {store_fee_rate}% - {total_agent_fee_rate}% = {admin_fee_rate}%")
            
            # 해당 매장에 대한 관리자 수수료 계산
            store_admin_fee = math.floor(daily_total * admin_fee_rate / 100)
            total_fee += store_admin_fee
            
            print(f"해당 매장 관리자 수수료: {daily_total:,} × {admin_fee_rate}% = {store_admin_fee:,}원")
        
        print(f"\n=== 최종 관리자 수수료 ===")
        print(f"총 관리자 수수료: {total_fee:,}원")
        
        # 함수로 계산한 결과와 비교
        calculated_fee = compute_downline_fee(admin_user, start_dt, end_dt)
        print(f"\n=== 함수 계산 결과 ===")
        print(f"compute_downline_fee 결과: {calculated_fee:,}원")
        
        if calculated_fee == total_fee:
            print("✅ 계산 결과가 일치합니다!")
        else:
            print("❌ 계산 결과가 다릅니다!")

if __name__ == "__main__":
    debug_admin_fee() 