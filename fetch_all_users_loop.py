import asyncio
import time
from pyrogram import Client
from models import db, User, Transaction
from flask import Flask
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

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
    if not user.telegram_group:
        return
    try:
        async for msg in app_client.get_chat_history(int(user.telegram_group), limit=100):
            if not msg.text:
                continue
            if msg.date < start_date:
                continue
            parsed = parse_message(msg.text)
            if not parsed:
                continue
            ttype, amount, balance, sender = parsed

            # 중복 검사: 날짜, 입금/출금, 금액, 보낸사람이 모두 동일한지 확인
            exists = Transaction.query.filter_by(
                user_id=user.id,
                type=ttype,
                amount=amount,
                sender=sender,
                timestamp=msg.date
            ).first()

            if exists:
                continue  # 중복된 거래는 저장하지 않음

            # 새 거래 저장
            t = Transaction(
                user_id=user.id,
                type=ttype,
                amount=amount,
                balance=balance,
                notification_balance=balance,  # 텔레그램에서 파싱한 잔액을 알림잔액으로 저장
                sender=sender,
                timestamp=msg.date
            )
            db.session.add(t)
            db.session.commit()
            print(f"✅ 저장됨: {msg.date} ({user.username}) - {amount}원 ({ttype})")
    except Exception as e:
        print(f"❌ 오류 ({user.username}):", e)

async def main_loop():
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app_client:
        while True:
            with app.app_context():
                users = User.query.filter(User.telegram_group != None).all()
                for user in users:
                    await fetch_for_user(app_client, user)
            await asyncio.sleep(60)

if __name__ == "__main__":
    with app.app_context():
        asyncio.run(main_loop())
