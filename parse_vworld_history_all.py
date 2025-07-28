import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

from models import User, Transaction

# Telegram API 설정
api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"
session_name = "my_account"

# DB 연결
engine = create_engine("sqlite:///bank.db")
Session = sessionmaker(bind=engine)

# 메시지 파싱 함수
def parse_message(text):
    try:
        lines = text.strip().splitlines()

        # 💡 첫 줄이 백*(xxxx) 형태면 제거
        if lines and re.match(r"^백\*\(\d+\)", lines[0]):
            lines = lines[1:]

        if len(lines) < 3:
            return None

        type_ = "입금" if "입금" in lines[0] else "출금" if "출금" in lines[0] else None
        if not type_:
            return None

        amount = int(re.sub(r"[^\d]", "", lines[0]))
        balance = int(re.sub(r"[^\d]", "", lines[1]))
        sender = lines[2].strip()

        return {"type": type_, "amount": amount, "balance": balance, "sender": sender}
    except Exception as e:
        print(f"❌ 파싱 실패: {e}")
        return None

# 전체 메시지 수집
async def fetch_all_vworld_history():
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
        cutoff_start = datetime(2024, 7, 16)
        cutoff_end = datetime(2024, 7, 20, 23, 59, 59)
        chat_id = -1002658267526
        offset_id = 0
        try:
        while True:
            messages = await app.get_chat_history(chat_id, offset_id=offset_id, limit=100)
            if not messages:
                break
            for msg in messages:
                offset_id = msg.message_id
                print('📬 받은 메시지 날짜:', msg.date)
                if msg.date < cutoff_start:
                    break
                if msg.date > cutoff_end:
                    continue
                if not msg.text:
                    continue
                parsed = parse_message(msg.text)
                if not parsed:
                    continue
                session = Session()
                exists = session.query(Transaction).filter_by(timestamp=msg.date).first()
                if exists:
                    session.close()
                    continue
                transaction = Transaction(
                    user_id=None,
                    type=parsed['type'],
                    amount=parsed['amount'],
                    balance=parsed['balance'],
                    sender=parsed['sender'],
                    timestamp=msg.date
                )
                session.add(transaction)
                session.commit()
                session.close()
                print('✅ 저장 완료:', msg.date)
                await asyncio.sleep(0.5)