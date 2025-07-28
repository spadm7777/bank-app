#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
일일수수료 타입을 입금으로 변경하는 스크립트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FeeLog

def fix_daily_fee_to_deposit():
    """일일수수료 타입을 입금으로 변경합니다."""
    
    with app.app_context():
        print("=== 일일수수료를 입금으로 변경 ===")
        
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
            
            # '일일수수료' 타입인 로그들 확인
            daily_fee_logs = [log for log in fee_logs if log.type == '일일수수료']
            
            if not daily_fee_logs:
                print("  일일수수료 로그가 없습니다.")
                continue
            
            print(f"  수정할 일일수수료 로그: {len(daily_fee_logs)}개")
            
            for log in daily_fee_logs:
                timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                old_type = log.type
                old_description = log.description
                
                # 타입을 '입금'으로 변경
                log.type = '입금'
                
                # 설명도 수정 (일일수수료 → 수수료 입금)
                if '일일 수수료' in log.description:
                    log.description = log.description.replace('일일 수수료', '수수료 입금')
                
                print(f"    {timestamp_str}: {old_type} → 입금 ({log.amount:,}원)")
                print(f"      설명: {old_description} → {log.description}")
                
                total_fixed += 1
        
        # 변경사항 커밋
        db.session.commit()
        print(f"\n✅ 총 {total_fixed}개의 일일수수료 로그를 입금으로 변경 완료!")
        
        # 수정 후 결과 확인
        print(f"\n=== 수정 후 결과 확인 ===")
        for user in users:
            fee_logs = FeeLog.query.filter_by(user_id=user.id).order_by(FeeLog.timestamp.asc()).all()
            if fee_logs:
                daily_fee_logs = [log for log in fee_logs if log.type == '일일수수료']
                if daily_fee_logs:
                    print(f"\n{user.username} ({user.role}) - 아직 일일수수료 로그가 있습니다:")
                    for log in daily_fee_logs:
                        timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"  {timestamp_str}: {log.amount:,}원 - {log.description}")
                else:
                    print(f"\n{user.username} ({user.role}): 모든 로그가 입금으로 변경됨")

if __name__ == '__main__':
    fix_daily_fee_to_deposit() 