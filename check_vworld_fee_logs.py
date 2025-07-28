#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vworld 매장의 거래내역과 수수료 로그 상태 확인 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee

def check_vworld_fee_logs():
    """vworld 매장의 거래내역과 수수료 로그 상태를 확인합니다."""
    
    with app.app_context():
        print("=== vworld 매장 거래내역 및 수수료 로그 상태 확인 ===")
        
        # vworld 사용자 조회
        user = User.query.filter_by(username='vworld').first()
        if not user:
            print("vworld 사용자를 찾을 수 없습니다.")
            return
        
        print(f"사용자: {user.username} ({user.role})")
        print(f"수수료율: {user.fee_rate}%")
        
        # 거래내역 확인
        transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp).all()
        print(f"총 거래내역: {len(transactions)}개")
        
        if transactions:
            first_tx = transactions[0]
            last_tx = transactions[-1]
            print(f"첫 거래: {first_tx.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"마지막 거래: {last_tx.timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        # 날짜별 거래내역 확인
        date_transactions = {}
        for tx in transactions:
            date = tx.timestamp.date()
            if date not in date_transactions:
                date_transactions[date] = []
            date_transactions[date].append(tx)
        
        print(f"\n날짜별 거래내역:")
        for date in sorted(date_transactions.keys()):
            daily_txs = date_transactions[date]
            daily_deposits = [tx for tx in daily_txs if tx.type == '입금']
            daily_withdraws = [tx for tx in daily_txs if tx.type == '출금']
            daily_deposit_total = sum(tx.amount for tx in daily_deposits)
            daily_withdraw_total = sum(tx.amount for tx in daily_withdraws)
            print(f"  {date}: 입금 {len(daily_deposits)}건 ({daily_deposit_total:,}원), 출금 {len(daily_withdraws)}건 ({daily_withdraw_total:,}원)")
        
        # 수수료 로그 확인
        fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp).all()
        print(f"\n현재 수수료 로그: {len(fee_logs)}개")
        
        if fee_logs:
            first_log = fee_logs[0]
            last_log = fee_logs[-1]
            print(f"첫 수수료 로그: {first_log.timestamp.strftime('%Y-%m-%d')} - {first_log.amount:,}원")
            print(f"마지막 수수료 로그: {last_log.timestamp.strftime('%Y-%m-%d')} - {last_log.amount:,}원")
        
        # 날짜별 수수료 로그 확인
        logged_dates = {log.timestamp.date() for log in fee_logs}
        print(f"\n수수료 로그가 기록된 날짜: {sorted(logged_dates)}")
        
        # 누락된 날짜 확인
        missing_dates = []
        for date in sorted(date_transactions.keys()):
            if date not in logged_dates:
                missing_dates.append(date)
        
        print(f"\n수수료 로그가 누락된 날짜: {missing_dates}")
        print(f"누락된 날짜 수: {len(missing_dates)}개")

if __name__ == "__main__":
    check_vworld_fee_logs() 