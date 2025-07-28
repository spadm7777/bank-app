#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin의 2025.07.27 로그를 찾는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def find_admin_log():
    """Admin의 2025.07.27 로그를 찾습니다."""
    
    with app.app_context():
        print("=== Admin 2025.07.27 로그 찾기 ===")
        
        # admin 사용자 조회
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 2025.07.27 날짜의 모든 로그 찾기
        start_date = datetime(2025, 7, 27, 0, 0)
        end_date = datetime(2025, 7, 28, 0, 0)
        
        logs = FeeLog.query.filter(
            FeeLog.user_id == admin.id,
            FeeLog.timestamp >= start_date,
            FeeLog.timestamp < end_date
        ).order_by(FeeLog.timestamp.asc()).all()
        
        print(f"2025.07.27 로그 개수: {len(logs)}")
        
        for log in logs:
            print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {log.amount:,}원 - {log.balance:,}원 - {log.description}")
        
        # 모든 로그 확인
        all_logs = FeeLog.query.filter_by(user_id=admin.id).order_by(FeeLog.timestamp.desc()).limit(5).all()
        print(f"\n최근 5개 로그:")
        for log in all_logs:
            print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {log.amount:,}원 - {log.balance:,}원 - {log.description}")

if __name__ == '__main__':
    find_admin_log() 