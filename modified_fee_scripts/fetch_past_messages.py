import re
import asyncio
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pyrogram import Client
from models import User, Transaction
from db import db
from flask import Flask

# 텔레그램 API 설정
api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"
app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Flask 앱 설정
flask_app = Flask(__name__)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(flask_app)

def parse_message(text: str, msg_date: datetime) -> dict | None:
    text = text.strip()
    match = re.search(r'(입금|출금)\s*([\d,]+)원\s*잔액\s*([\d,]+)원\s*(.+)$', text)
    if not match:
        return None
    try:
        return {
            'timestamp': msg_date,
            'type': match.group(1),
            'amount': int(match.group(2).replace(',', '')),
            'balance': int(match.group(3).replace(',', '')),
            'sender': match.group(4).strip()
        }
    except Exception as e:
        print(f"⚠️ 파싱 예외: {e}")
        return None

async def fetch_and_save_messages():
    Session = sessionmaker(bind=db.engine)
    session = Session()
    try:
        await app.start()
        users = session.query(User).filter(User.telegram_group != None).all()
        for user in users:
            print(f"\n👤 유저: {user.username}, Chat ID: {user.telegram_group}")
            try:
                chat_id = int(user.telegram_group.strip())
                chat = await app.get_chat(chat_id)
                print(f"✅ 그룹 접근 성공: {chat.title}")

                async for msg in app.get_chat_history(chat.id, limit=50):
                    if not msg.text:
                        continue
                    print(f"📩 메시지: {msg.text}")
                    data = parse_message(msg.text, msg.date)
                    if data:
                        print(f"✅ 파싱됨: {data}")
                        exists = session.query(Transaction).filter_by(
                            timestamp=data['timestamp'],
                            type=data['type'],
                            amount=data['amount'],
                            balance=data['balance'],
                            sender=data['sender'],
                            user_id=user.id
                        ).first()
                        if not exists:
                            print("📝 새 거래 저장")
                            session.add(Transaction(
                                user_id=user.id,
                                timestamp=data['timestamp'],
                                type=data['type'],
                                amount=data['amount'],
                                balance=data['balance'],
                                sender=data['sender'],
                                fee=int(data['amount'] * 0.005) if data['type'] == '입금' else 0
                            ))
                        else:
                            print("🔁 중복 거래 (저장 안 함)")
                    else:
                        print("❌ 파싱 실패")
                session.commit()
            except Exception as e:
                print(f"❌ 그룹 접근 실패 또는 메시지 오류: {e}")
    finally:
        await app.stop()
        session.close()

async def run_every_minute():
    while True:
        print(f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 메시지 수집 시작")
        await fetch_and_save_messages()
        print("✅ 수집 완료. 60초 대기")
        await asyncio.sleep(60)

if __name__ == '__main__':
    with flask_app.app_context():
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_every_minute())
