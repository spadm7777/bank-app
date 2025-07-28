#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
기존 수수료 로그들의 timestamp를 확인하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def check_fee_log_timestamps():
    """기존 수수료 로그들의 timestamp를 확인합니다."""
    
    with app.app_context():
        print("=== 기존 수수료 로그 timestamp 확인 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # admin의 수수료 로그 조회
        fee_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.asc()).all()
        
        print(f"총 {len(fee_logs)}개의 수수료 로그가 있습니다.")
        print()
        
        print("날짜/시간                구분         금액           잔액           설명")
        print("-" * 100)
        
        for log in fee_logs:
            timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp_str:<20} {log.type:<10} {log.amount:>10,}원 {log.balance:>10,}원 {log.description}")
        
        print()
        
        # 00:00:00으로 설정된 로그들 확인
        zero_time_logs = [log for log in fee_logs if log.timestamp.hour == 0 and log.timestamp.minute == 0 and log.timestamp.second == 0]
        
        print(f"00:00:00으로 설정된 로그: {len(zero_time_logs)}개")
        if zero_time_logs:
            print("다음 로그들이 00:00:00으로 설정되어 있습니다:")
            for log in zero_time_logs:
                print(f"  {log.timestamp.strftime('%Y-%m-%d')} - {log.amount:,}원")

if __name__ == '__main__':
    check_fee_log_timestamps() 