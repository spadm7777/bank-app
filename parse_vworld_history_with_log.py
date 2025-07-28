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
        session = Session()
        user = session.query(User).filter_by(username="vworld").first()

        if not user or not user.telegram_group:
            print("❌ 'vworld' 유저 또는 telegram_group이 설정되지 않았습니다.")
            return

        chat_id = user.telegram_group
        cutoff_start = datetime(2024, 7, 16)
        cutoff_end = datetime(2024, 7, 20, 23, 59, 59)

        print(f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - vworld 최근 20일 메시지 수집 시작")
        total_saved = 0
        total_skipped = 0

        try:
            async for msg in app.get_chat_history(chat_id):
                print('📬 받은 메시지 날짜:', msg.date)
                if msg.date < cutoff_start or msg.date > cutoff_end:
                    break
                if not msg.text:
                    continue

                parsed = parse_message(msg.text)
                if not parsed:
                    continue

                exists = session.query(Transaction).filter_by(
                    user_id=user.id,
                    timestamp=msg.date,
                    amount=parsed["amount"],
                    sender=parsed["sender"]
                ).first()
                if exists:
                    total_skipped += 1
                    continue

                fee_rate = user.fee_rate or 0.5
                fee = int(parsed["amount"] * fee_rate / 100)

                tx = Transaction(
                    user_id=user.id,
                    type=parsed["type"],
                    amount=parsed["amount"],
                    balance=parsed["balance"],
                    sender=parsed["sender"],
                    timestamp=msg.date,
                    fee=fee
                )
                session.add(tx)
                total_saved += 1

                if total_saved % 100 == 0:
                    print(f"✅ 저장 {total_saved}건...")

                if total_saved % 200 == 0:
                    await asyncio.sleep(1)

            session.commit()
            print(f"🎉 완료: 저장 {total_saved}건, 중복 {total_skipped}건 생략됨")

        except FloodWait as e:
            print(f"🔒 요청 초과: {e.value}초 대기...")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"⚠️ 처리 오류: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    asyncio.run(fetch_all_vworld_history())