import re
import sys
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from sqlalchemy.orm import sessionmaker
from app import app
from db import db
from models import User, Transaction

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

def parse_message(text: str, msg_date: datetime) -> dict | None:
    text = text.strip()
    match = re.search(r'(입금|출금)\s*([\d,]+)원\s*잔액\s*([\d,]+)원\s*(.+)$', text)
    if not match:
        return None
    try:
        trans_type = match.group(1)
        amount = int(match.group(2).replace(',', ''))
        balance = int(match.group(3).replace(',', ''))
        sender = match.group(4).strip()
        return {
            'timestamp': msg_date,
            'type': trans_type,
            'amount': amount,
            'balance': balance,
            'sender': sender
        }
    except Exception as e:
        print(f"파싱 실패: {e} / 텍스트: {text}")
        return None

async def fetch_past_messages(chat_name: str, limit_days: int):
    with app.app_context():
        Session = sessionmaker(bind=db.engine)
        session = Session()

        async with Client("my_account", api_id=api_id, api_hash=api_hash) as tg_client:
            try:
                chat = await tg_client.get_chat(chat_name)
                from_date = datetime.now() - timedelta(days=limit_days)

                user = session.query(User).filter_by(telegram_group=str(chat.id)).first()
                if not user:
                    print(f"채팅방 ID '{chat.id}' 와 연결된 사용자가 DB에 없습니다.")
                    return

                async for msg in tg_client.get_chat_history(chat.id, limit=1000):
                    if not msg.text:
                        continue
                    if msg.date < from_date:
                        break
                    data = parse_message(msg.text, msg.date)
                    if data:
                        exists = session.query(Transaction).filter_by(
                            timestamp=data['timestamp'],
                            type=data['type'],
                            amount=data['amount'],
                            balance=data['balance'],
                            sender=data['sender'],
                            user_id=user.id
                        ).first()
                        if not exists:
                            trans = Transaction(
                                user_id=user.id,
                                timestamp=data['timestamp'],
                                type=data['type'],
                                amount=data['amount'],
                                balance=data['balance'],
                                sender=data['sender'],
                                fee=0
                            )
                            session.add(trans)
                session.commit()

            except Exception as e:
                print(f"메시지 수집 중 오류: {e}")
            finally:
                session.close()

def main():
    if len(sys.argv) < 3:
        print("사용법: python telegram_fetch_past.py '<채팅방 ID 또는 이름>' <일수>")
        sys.exit(1)

    chat_name = sys.argv[1]
    limit_days = int(sys.argv[2])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(fetch_past_messages(chat_name, limit_days))
    finally:
        loop.close()

if __name__ == "__main__":
    main()
