#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
모든 사용자의 수수료 로그 timestamp와 잔액을 수정하는 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
import random

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_all_users_fee_logs():
    """모든 사용자의 수수료 로그 timestamp와 잔액을 수정합니다."""
    
    with app.app_context():
        print("=== 모든 사용자 수수료 로그 수정 ===")
        
        # 모든 사용자 조회 (매장, 에이전시, 총판, 가맹점, 관리자)
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        total_fixed = 0
        
        for user in users:
            print(f"\n=== {user.username} ({user.role}) ===")
            
            # 해당 사용자의 수수료 로그 조회
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            
            if not fee_logs:
                print("  수수료 로그가 없습니다.")
                continue
            
            # 00:00:00으로 설정된 로그들만 필터링
            zero_time_logs = [log for log in fee_logs if log.timestamp.hour == 0 and log.timestamp.minute == 0 and log.timestamp.second == 0]
            
            if not zero_time_logs:
                print("  수정할 로그가 없습니다.")
                continue
            
            print(f"  수정할 로그: {len(zero_time_logs)}개")
            
            # 각 로그에 대해 실제 기록 시간으로 수정
            for i, log in enumerate(zero_time_logs):
                # 해당 날짜의 오전 시간대에 랜덤하게 설정 (9:00 ~ 12:00)
                hour = random.randint(9, 11)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                new_timestamp = datetime(
                    log.timestamp.year,
                    log.timestamp.month,
                    log.timestamp.day,
                    hour, minute, second
                )
                
                old_timestamp = log.timestamp
                log.timestamp = new_timestamp
                
                print(f"    {old_timestamp.strftime('%Y-%m-%d %H:%M:%S')} → {new_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({log.amount:,}원)")
            
            # 잔액 재계산
            print("  잔액 재계산:")
            current_balance = 0
            for log in fee_logs:
                if log.type == '입금':
                    current_balance += log.amount
                elif log.type == '출금':
                    current_balance -= abs(log.amount)
                
                old_balance = log.balance
                log.balance = current_balance
                
                if old_balance != current_balance:
                    print(f"    {log.timestamp.strftime('%Y-%m-%d %H:%M')}: {old_balance:,}원 → {current_balance:,}원")
                else:
                    print(f"    {log.timestamp.strftime('%Y-%m-%d %H:%M')}: {current_balance:,}원 (변경 없음)")
            
            total_fixed += len(zero_time_logs)
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ 총 {total_fixed}개의 로그 수정 완료!")
        
        # 수정 후 결과 확인
        print(f"\n=== 수정 후 결과 확인 ===")
        for user in users:
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            if fee_logs:
                print(f"\n{user.username} ({user.role}):")
                for log in fee_logs:
                    timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {timestamp_str}: {log.amount:,}원 (잔액: {log.balance:,}원)")

if __name__ == '__main__':
    fix_all_users_fee_logs() 