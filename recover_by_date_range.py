
# recover_register_combined.py

import re
from datetime import datetime, timedelta
from app import app, db
from models import User, Transaction
from pyrogram import Client

# ✅ 설정
USERNAME = 'vworld'
CHAT_ID = -1002658267526
START_DATE = datetime(2025, 7, 16)
END_DATE = datetime(2025, 7, 26)

api_id = 26558422  # 🔁 여기에 본인 api_id 입력
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"  # 🔁 여기에 본인 api_hash 입력
session_name = "mysession"

# ✅ 메시지 파싱 함수
def parse_message(msg):
    pattern = r"(입금|출금)\s([\d,]+)원\s+잔액\s([\d,]+)원\s+(.+)"
    match = re.search(pattern, msg)
    if match:
        ttype = match.group(1)
        amount = int(match.group(2).replace(",", ""))
        balance = int(match.group(3).replace(",", ""))
        sender = match.group(4).strip()
        return ttype, amount, balance, sender
    return None

# ✅ 실행
with app.app_context():
    user = User.query.filter_by(username=USERNAME).first()
    if not user:
        print(f"[❌] 사용자 '{USERNAME}'를 찾을 수 없습니다.")
        exit()

    with Client(session_name, api_id=api_id, api_hash=api_hash) as app_client:
        try:
            chat = app_client.get_chat(CHAT_ID)
            print(f"[✅] 채팅방 등록됨: {chat.title}")
        except Exception as e:
            print(f"[❌] 채팅방 접근 실패: {e}")
            exit()

        count = 0
        for msg in app_client.get_chat_history(CHAT_ID, offset_date=END_DATE + timedelta(days=1)):
            if not (START_DATE <= msg.date <= END_DATE):
                continue
            if not msg.text:
                continue

            parsed = parse_message(msg.text)
            if not parsed:
                continue

            ttype, amount, balance, sender = parsed

            exists = Transaction.query.filter_by(
                user_id=user.id,
                amount=amount,
                balance=balance,
                sender=sender,
                timestamp=msg.date,
                type=ttype
            ).first()

            if not exists:
                new_tx = Transaction(
                    user_id=user.id,
                    type=ttype,
                    amount=amount,
                    balance=balance,
                    sender=sender,
                    timestamp=msg.date
                )
                db.session.add(new_tx)
                db.session.commit()
                print(f"[✅] 저장됨: {msg.date} | {ttype} | {amount} | {sender}")
                count += 1
            else:
                print(f"[⏩] 중복 생략: {msg.date} | {ttype} | {amount} | {sender}")

        print(f"📦 총 저장된 거래: {count}건")
