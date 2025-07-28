#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
기존 수수료 로그들의 timestamp를 실제 기록 시간으로 수정하는 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
import random

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_fee_log_timestamps():
    """기존 수수료 로그들의 timestamp를 실제 기록 시간으로 수정합니다."""
    
    with app.app_context():
        print("=== 기존 수수료 로그 timestamp 수정 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # admin의 수수료 로그 조회 (00:00:00으로 설정된 것들만)
        fee_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        # 00:00:00으로 설정된 로그들만 필터링
        zero_time_logs = [log for log in fee_logs if log.timestamp.hour == 0 and log.timestamp.minute == 0 and log.timestamp.second == 0]
        
        print(f"수정할 로그 수: {len(zero_time_logs)}개")
        
        if not zero_time_logs:
            print("수정할 로그가 없습니다.")
            return
        
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
            
            print(f"  {old_timestamp.strftime('%Y-%m-%d %H:%M:%S')} → {new_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({log.amount:,}원)")
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ {len(zero_time_logs)}개의 로그 timestamp 수정 완료!")
        
        # 수정 후 결과 확인
        print(f"\n=== 수정 후 결과 ===")
        updated_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        print("날짜/시간                구분         금액           잔액")
        print("-" * 80)
        
        for log in updated_logs:
            timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp_str:<20} {log.type:<10} {log.amount:>10,}원 {log.balance:>10,}원")

if __name__ == '__main__':
    fix_fee_log_timestamps() 