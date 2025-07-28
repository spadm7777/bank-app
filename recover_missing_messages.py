# recover_missing_messages.py

from datetime import datetime
from app import app, db  # ✅ app 직접 가져옴
from models import Transaction, User

# 설정값
USERNAME = 'vworld'
AMOUNT = 40000
BALANCE = 5519579
SENDER = '최승배'
TYPE = '입금'
TIMESTAMP = datetime(2024, 10, 21, 22, 24)

# DB 처리
with app.app_context():  # ✅ Flask 앱 컨텍스트 사용
    user = User.query.filter_by(username=USERNAME).first()
    if not user:
        print(f"[❌] 사용자 '{USERNAME}'를 찾을 수 없습니다.")
    else:
        exists = Transaction.query.filter_by(
            user_id=user.id,
            amount=AMOUNT,
            timestamp=TIMESTAMP,
            type=TYPE
        ).first()

        if exists:
            print(f"[ℹ️] 이미 존재하는 내역: {exists.timestamp}, {exists.sender}, {exists.amount}")
        else:
            new_tx = Transaction(
                user_id=user.id,
                type=TYPE,
                amount=AMOUNT,
                balance=BALANCE,
                sender=SENDER,
                timestamp=TIMESTAMP
            )
            db.session.add(new_tx)
            db.session.commit()
            print(f"[✅] 누락된 거래내역 복구 완료: {TIMESTAMP}, {SENDER}, {AMOUNT}원")
