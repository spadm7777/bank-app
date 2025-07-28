# telegram_client.py

import os
import asyncio
import re
from pyrogram import Client
from pyrogram.errors import FloodWait
from dotenv import load_dotenv
from datetime import datetime
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 환경변수 불러오기
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
GROUP_NAME = os.getenv("GROUP_NAME")

# DB 초기화
def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            type TEXT,
            amount INTEGER,
            balance INTEGER,
            sender TEXT
        )
    """)
    conn.commit()
    conn.close()

# 메시지 파싱
def parse_message(text: str):
    lines = text.strip().split("\n")
    if len(lines) != 4:
        return None  # 메시지가 4줄이 아니면 무시

    type_line = lines[1].strip()
    balance_line = lines[2].strip()
    sender_name = lines[3].strip()

    if "입금" in type_line:
        trans_type = "입금"
    elif "출금" in type_line:
        trans_type = "출금"
    else:
        return None

    # 금액과 잔액 숫자만 추출
    amount_match = re.search(r"(\d[\d,]*)원", type_line)
    balance_match = re.search(r"(\d[\d,]*)원", balance_line)

    if not amount_match or not balance_match:
        return None

    amount = int(amount_match.group(1).replace(",", ""))
    balance = int(balance_match.group(1).replace(",", ""))

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": trans_type,
        "amount": amount,
        "balance": balance,
        "sender": sender_name
    }

# 메시지 저장
def save_to_db(data):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (timestamp, type, amount, balance, sender)
        VALUES (?, ?, ?, ?, ?)
    """, (data['timestamp'], data['type'], data['amount'], data['balance'], data['sender']))
    conn.commit()
    conn.close()

# 텔레그램 클라이언트
app = Client("my_account", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)

# 메시지 수집 작업
async def fetch_messages():
    async with app:
        async for dialog in app.get_dialogs():
            if GROUP_NAME in dialog.chat.title:
                group_id = dialog.chat.id
                break
        else:
            print("지정한 그룹을 찾을 수 없습니다.")
            return

        async for msg in app.get_chat_history(group_id, limit=10):
            if msg.text:
                parsed = parse_message(msg.text)
                if parsed:
                    save_to_db(parsed)
                    print(f"저장됨: {parsed}")

# 1분마다 실행 스케줄러
async def run_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_messages, "interval", minutes=1)
    scheduler.start()
    print("📡 메시지 수집 시작됨 (1분마다 확인)")
    while True:
        await asyncio.sleep(3600)

# 메인 실행
if __name__ == "__main__":
    init_db()
    asyncio.run(run_scheduler())
