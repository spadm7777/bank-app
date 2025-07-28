#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sik과 busan의 수수료 계산 디버깅 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def debug_fee_calculation():
    """sik과 busan의 수수료 계산을 디버깅합니다."""
    
    with app.app_context():
        print("=== sik과 busan 수수료 계산 디버깅 ===")
        
        # sik과 busan 사용자 조회
        sik_user = User.query.filter_by(username='sik').first()
        busan_user = User.query.filter_by(username='busan').first()
        
        if not sik_user:
            print("❌ sik 사용자를 찾을 수 없습니다.")
            return
        if not busan_user:
            print("❌ busan 사용자를 찾을 수 없습니다.")
            return
            
        print(f"\n=== sik 사용자 정보 ===")
        print(f"사용자명: {sik_user.username}")
        print(f"등급: {sik_user.role}")
        print(f"수수료율: {sik_user.fee_rate}%")
        
        print(f"\n=== busan 사용자 정보 ===")
        print(f"사용자명: {busan_user.username}")
        print(f"등급: {busan_user.role}")
        print(f"수수료율: {busan_user.fee_rate}%")
        
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
        
        # sik의 하위 매장들
        sik_descendants = get_descendants(sik_user)
        sik_stores = [child for child in sik_descendants if child.role == '매장']
        print(f"\n=== sik의 하위 매장들 ({len(sik_stores)}개) ===")
        for child in sik_stores:
            print(f"  - {child.username} (등급: {child.role}, 수수료율: {child.fee_rate}%)")
            
            # 하위 매장의 일일 입금액 확인
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == child.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            
            daily_total = sum(tx.amount for tx in daily_deposits)
            print(f"    일일 총 입금액: {daily_total:,}원")
            
            if daily_total > 0:
                child_fee = daily_total * (child.fee_rate or 0) / 100
                print(f"    생성된 수수료: {child_fee:,}원")
        
        # busan의 하위 매장들
        busan_descendants = get_descendants(busan_user)
        busan_stores = [child for child in busan_descendants if child.role == '매장']
        print(f"\n=== busan의 하위 매장들 ({len(busan_stores)}개) ===")
        for child in busan_stores:
            print(f"  - {child.username} (등급: {child.role}, 수수료율: {child.fee_rate}%)")
            
            # 하위 매장의 일일 입금액 확인
            daily_deposits = Transaction.query.filter(
                Transaction.user_id == child.id,
                Transaction.type == '입금',
                Transaction.timestamp >= start_dt,
                Transaction.timestamp < end_dt
            ).all()
            
            daily_total = sum(tx.amount for tx in daily_deposits)
            print(f"    일일 총 입금액: {daily_total:,}원")
            
            if daily_total > 0:
                child_fee = daily_total * (child.fee_rate or 0) / 100
                print(f"    생성된 수수료: {child_fee:,}원")
        
        # 수수료 계산 결과
        sik_fee = compute_downline_fee(sik_user, start_dt, end_dt)
        busan_fee = compute_downline_fee(busan_user, start_dt, end_dt)
        
        print(f"\n=== 최종 수수료 계산 결과 ===")
        print(f"sik: {sik_fee:,}원")
        print(f"busan: {busan_fee:,}원")
        
        if sik_fee != busan_fee:
            print(f"\n⚠️  수수료가 다른 이유:")
            print(f"  - sik과 busan의 하위 매장 구조가 다름")
            print(f"  - 하위 매장들의 일일 총 입금액이 다름")
            print(f"  - 수수료 분배 로직에서 상위 계정들의 수수료율이 다름")

if __name__ == "__main__":
    debug_fee_calculation() 