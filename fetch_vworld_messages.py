
import asyncio
from pyrogram import Client
from models import db, Transaction, User
from flask import Flask
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

api_id = 26558422      # 🔁 여기에 실제 api_id 입력
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"  # 🔁 여기에 실제 api_hash 입력
session_name = "vworld_session"
chat_id = -2658267526
start_date = datetime(2025, 2, 16)
end_date = datetime.now()

def parse_message(text):
    lines = text.strip().split('\n')
    if len(lines) < 3:
        return None
    if '입금' in lines[1] or '출금' in lines[1]:
        try:
            ttype = '입금' if '입금' in lines[1] else '출금'
            amount = int(lines[1].split()[1].replace(',', '').replace('원', ''))
            balance = int(lines[2].split()[1].replace(',', '').replace('원', ''))
            sender = lines[3] if len(lines) > 3 else ''
            return ttype, amount, balance, sender
        except:
            return None
    return None

async def fetch_and_store():
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app_client:
        async for msg in app_client.get_chat_history(chat_id):
            if not msg.text:
                continue
            if not (start_date <= msg.date <= end_date):
                continue
            parsed = parse_message(msg.text)
            if not parsed:
                continue
            with app.app_context():
                exists = Transaction.query.filter_by(timestamp=msg.date).first()
                if exists:
                    continue
                ttype, amount, balance, sender = parsed
                t = Transaction(
                    user_id=1,
                    type=ttype,
                    amount=amount,
                    balance=balance,
                    sender=sender,
                    timestamp=msg.date
                )
                db.session.add(t)
                db.session.commit()
                print("✅ 저장됨:", msg.date, "-", amount, "원 (", ttype, ")")

if __name__ == '__main__':
    with app.app_context():
        asyncio.run(fetch_and_store())
