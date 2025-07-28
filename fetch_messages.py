# fetch_messages.py

import re
import asyncio
from datetime import datetime
from pyrogram import Client
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

api_id = 26558422  # 본인 api_id
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"  # 본인 api_hash

app = Client("my_account", api_id=api_id, api_hash=api_hash)

engine = create_engine('sqlite:///transactions.db', echo=False, connect_args={"check_same_thread": False})
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(String(20))   # 저장용 전체 시간
    type = Column(String(10))
    amount = Column(Integer)
    balance = Column(Integer)
    sender = Column(String(50))

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def parse_message(text: str, msg_date) -> dict | None:
    lines = text.strip().split('\n')
    if len(lines) < 4:
        return None

    type_line = lines[1]
    balance_line = lines[2]
    sender_line = lines[3]

    if '입금' in type_line:
        trans_type = '입금'
    elif '출금' in type_line:
        trans_type = '출금'
    else:
        return None

    try:
        amount = int(re.sub(r'[^\d]', '', type_line))
        balance = int(re.sub(r'[^\d]', '', balance_line))
        sender = sender_line.strip()
        timestamp_str = msg_date.strftime('%Y-%m-%d %H:%M:%S')
        date_only = msg_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"⚠️ 파싱 실패: {e}")
        return None

    return {
        'timestamp': timestamp_str,
        'date_only': date_only,
        'type': trans_type,
        'amount': amount,
        'balance': balance,
        'sender': sender
    }

async def main():
    await app.start()
    print("✅ 텔레그램 클라이언트 시작됨")

    session = Session()
    chat_id = "-1002658267526"  # 본인 채팅방 ID

    async for msg in app.get_chat_history(chat_id, limit=100):
        if not msg.text:
            continue

        data = parse_message(msg.text, msg.date)
        if data:
            # 날짜만 비교한 중복 차단
            exists = session.query(Transaction).filter(
                Transaction.type == data['type'],
                Transaction.amount == data['amount'],
                Transaction.balance == data['balance'],
                Transaction.sender == data['sender'],
                Transaction.timestamp.like(f"{data['date_only']}%")
            ).first()

            if not exists:
                session.add(Transaction(
                    timestamp=data['timestamp'],
                    type=data['type'],
                    amount=data['amount'],
                    balance=data['balance'],
                    sender=data['sender']
                ))
                print(f"✅ 저장됨: {data}")
            else:
                print(f"⏩ 중복 생략: {data}")

    session.commit()
    session.close()
    print("📦 DB 커밋 완료")

    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
