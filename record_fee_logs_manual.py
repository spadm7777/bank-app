#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수동으로 수수료 로그를 기록하는 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Transaction, FeeLog, compute_downline_fee, record_missing_logs

def record_fee_logs_manual():
    """수동으로 수수료 로그를 기록합니다."""
    
    with app.app_context():
        print("=== 수동 수수료 로그 기록 ===")
        
        # 누락된 수수료 로그 기록
        record_missing_logs()
        
        print("✅ 수수료 로그 기록 완료")
        
        # 기록 후 상태 확인
        users = User.query.filter(User.role.in_(['매장', '에이전시', '총판', '가맹점', '관리자'])).all()
        
        for user in users:
            fee_logs = FeeLog.query.filter_by(user_id=user.id).all()
            print(f"{user.username} ({user.role}): {len(fee_logs)}개 로그")

if __name__ == "__main__":
    record_fee_logs_manual() 