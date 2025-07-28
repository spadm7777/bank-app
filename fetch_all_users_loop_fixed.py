import asyncio
import time
import sqlite3
from pyrogram import Client
from datetime import datetime
import os

# 별도의 데이터베이스 연결 사용
def get_db_connection():
    conn = sqlite3.connect('instance/bank.db', timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def check_transaction_exists(conn, user_id, ttype, amount, sender, timestamp):
    """거래가 이미 존재하는지 확인"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM transactions 
        WHERE user_id = ? AND type = ? AND amount = ? AND sender = ? AND timestamp = ?
    """, (user_id, ttype, amount, sender, timestamp))
    return cursor.fetchone() is not None

def save_transaction(conn, user_id, ttype, amount, balance, sender, timestamp):
    """새 거래 저장"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, type, amount, balance, notification_balance, sender, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, ttype, amount, balance, balance, sender, timestamp))
    conn.commit()
    print(f"✅ 저장됨: {timestamp} - {amount}원 ({ttype}) - 알림잔액: {balance:,}원")

def get_users_with_telegram():
    """텔레그램 그룹이 있는 사용자들 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, telegram_group FROM users WHERE telegram_group IS NOT NULL")
    users = cursor.fetchall()
    conn.close()
    return users

api_id = 123456  # 🔁 본인의 API ID
api_hash = "your_api_hash"  # 🔁 본인의 API HASH
session_name = "vworld_session"
start_date = datetime(2025, 2, 16)

def parse_message(text):
    lines = text.strip().split('\n')
    
    # 백*(xxxx) 형태의 첫 줄 제거
    if lines and lines[0].startswith('백*('):
        lines = lines[1:]
    
    if len(lines) < 3:
        return None
    
    # 입금/출금 라인 찾기
    type_line = None
    for line in lines:
        if '입금' in line or '출금' in line:
            type_line = line
            break
    
    if not type_line:
        return None
    
    try:
        ttype = '입금' if '입금' in type_line else '출금'
        amount = int(type_line.split()[1].replace(',', '').replace('원', ''))
        
        # 잔액 라인 찾기 (정확히 "잔액"으로 시작하는 라인)
        balance_line = None
        for line in lines:
            if line.strip().startswith('잔액'):
                balance_line = line
                break
        
        if not balance_line:
            return None
            
        # "잔액" 다음의 숫자를 추출
        balance_text = balance_line.replace('잔액', '').strip()
        balance = int(balance_text.replace(',', '').replace('원', ''))
        
        # 보낸사람은 마지막 라인
        sender = lines[-1].strip()
        
        return ttype, amount, balance, sender
    except Exception as e:
        print("⚠️ 파싱 실패:", e)
        return None

async def fetch_for_user(app_client, user):
    if not user['telegram_group']:
        return
    
    conn = get_db_connection()
    try:
        async for msg in app_client.get_chat_history(int(user['telegram_group']), limit=100):
            if not msg.text:
                continue
            if msg.date < start_date:
                continue
            
            parsed = parse_message(msg.text)
            if not parsed:
                continue
            
            ttype, amount, balance, sender = parsed

            # 중복 검사
            if check_transaction_exists(conn, user['id'], ttype, amount, sender, msg.date):
                continue  # 중복된 거래는 저장하지 않음

            # 새 거래 저장
            save_transaction(conn, user['id'], ttype, amount, balance, sender, msg.date)
            
    except Exception as e:
        print(f"❌ 오류 ({user['username']}):", e)
    finally:
        conn.close()

async def main_loop():
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app_client:
        while True:
            try:
                users = get_users_with_telegram()
                for user in users:
                    await fetch_for_user(app_client, user)
            except Exception as e:
                print(f"❌ 메인 루프 오류: {e}")
            
            await asyncio.sleep(60)  # 1분마다 실행

if __name__ == "__main__":
    print("🚀 fetch_all_users_loop_fixed.py 시작...")
    print("📱 텔레그램 메시지 파싱 중...")
    asyncio.run(main_loop()) 