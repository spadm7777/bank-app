#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
모든 사용자의 수수료 로그에서 type이 '일일수수료'인 로그들을 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def check_fee_log_types():
    """모든 사용자의 수수료 로그에서 type이 '일일수수료'인 로그들을 확인합니다."""
    
    with app.app_context():
        print("=== 일일수수료 타입 로그 확인 ===")
        
        # 모든 사용자 조회 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        total_daily_fee_logs = 0
        
        for user in users:
            print(f"\n=== {user.username} ({user.role}) ===")
            
            # 해당 사용자의 수수료 로그 조회
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                continue
            
            # '일일수수료' 타입인 로그들 확인
            daily_fee_logs = [log for log in fee_logs if log.type == '일일수수료']
            
            if daily_fee_logs:
                print(f"  일일수수료 로그: {len(daily_fee_logs)}개")
                for log in daily_fee_logs:
                    timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"    {timestamp_str}: {log.amount:,}원 (잔액: {log.balance:,}원) - {log.description}")
                total_daily_fee_logs += len(daily_fee_logs)
            else:
                print("  일일수수료 로그가 없습니다.")
            
            # '입금' 타입인 로그들도 확인
            deposit_logs = [log for log in fee_logs if log.type == '입금']
            print(f"  입금 로그: {len(deposit_logs)}개")
        
        print(f"\n=== 전체 요약 ===")
        print(f"총 일일수수료 로그: {total_daily_fee_logs}개")
        
        if total_daily_fee_logs > 0:
            print("일일수수료를 입금으로 변경해야 합니다.")

if __name__ == '__main__':
    check_fee_log_types() 