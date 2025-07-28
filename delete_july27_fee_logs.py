#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
7월 27일의 모든 수수료 로그를 삭제하는 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog

def delete_july27_fee_logs():
    """7월 27일의 모든 수수료 로그를 삭제합니다."""
    
    with app.app_context():
        print("=== 7월 27일 수수료 로그 삭제 ===")
        
        # 7월 27일 날짜 설정
        target_date = datetime(2025, 7, 27).date()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        
        print(f"📅 {target_date.strftime('%Y-%m-%d')} 수수료 로그 삭제 시작...")
        
        # 7월 27일의 모든 수수료 로그 조회
        fee_logs = FeeLog.query.filter(
            FeeLog.timestamp >= start_dt,
            FeeLog.timestamp < end_dt
        ).all()
        
        print(f"삭제할 수수료 로그 개수: {len(fee_logs)}개")
        
        if fee_logs:
            # 사용자별로 그룹화하여 표시
            user_logs = {}
            for log in fee_logs:
                user = User.query.get(log.user_id)
                username = user.username if user else f"User{log.user_id}"
                if username not in user_logs:
                    user_logs[username] = []
                user_logs[username].append(log)
            
            print("\n삭제할 로그 목록:")
            for username, logs in user_logs.items():
                total_amount = sum(log.amount for log in logs)
                print(f"  {username}: {len(logs)}개 로그, 총 {total_amount:,}원")
            
            # 삭제 실행
            for log in fee_logs:
                db.session.delete(log)
            
            db.session.commit()
            print(f"\n✅ {len(fee_logs)}개의 수수료 로그가 삭제되었습니다.")
        else:
            print("삭제할 수수료 로그가 없습니다.")
        
        # 삭제 후 확인
        remaining_logs = FeeLog.query.filter(
            FeeLog.timestamp >= start_dt,
            FeeLog.timestamp < end_dt
        ).all()
        
        print(f"삭제 후 남은 7월 27일 로그: {len(remaining_logs)}개")

if __name__ == "__main__":
    delete_july27_fee_logs() 