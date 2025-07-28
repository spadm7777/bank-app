import re
import asyncio
from pyrogram import Client, filters
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import logging

# --- 설정값 (필요시 .env 등에서 읽도록 변경 가능) ---
api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"
chat_id = -1002658267526  # 모니터링할 텔레그램 단체방 ID (정수형으로)

# --- Pyrogram 클라이언트 초기화 ---
app = Client("my_account", api_id=api_id, api_hash=api_hash)

# --- DB 설정 및 모델 정의 ---
engine = create_engine('sqlite:///transactions.db', echo=False, connect_args={"check_same_thread": False})
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(String(20))  # 'YYYY-MM-DD HH:MM:SS' 형태
    type = Column(String(10))       # 입금 or 출금
    amount = Column(Integer)
    balance = Column(Integer)
    sender = Column(String(50))

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 메시지 파싱 함수 ---
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
    except Exception as e:
        logger.error(f"파싱 실패: {e}")
        return None

    return {
        'timestamp': timestamp_str,
        'type': trans_type,
        'amount': amount,
        'balance': balance,
        'sender': sender
    }

# --- 메시지 이벤트 핸들러 ---
@app.on_message(filters.chat(chat_id) & filters.text)
async def message_handler(client, message):
    session = Session()
    try:
        data = parse_message(message.text, message.date)
        if data:
            exists = session.query(Transaction).filter_by(
                timestamp=data['timestamp'],
                type=data['type'],
                amount=data['amount'],
                balance=data['balance'],
                sender=data['sender']
            ).first()
            if not exists:
                session.add(Transaction(**data))
                session.commit()
                logger.info(f"새 메시지 저장됨: {data}")
    except Exception as e:
        logger.error(f"메시지 처리 중 오류: {e}")
    finally:
        session.close()

# --- 클라이언트 실행 및 안정적 재접속 함수 ---
async def run_client():
    while True:
        try:
            logger.info("텔레그램 클라이언트 시작 중...")
            await app.start()
            logger.info("메시지 모니터링 중... (종료하려면 Ctrl+C)")
            from pyrogram import idle
            await idle()  # 무한 대기 상태 유지
        except Exception as e:
            logger.error(f"예외 발생: {e}. 10초 후 재시작합니다.")
            await app.stop()
            await asyncio.sleep(10)
        else:
            break

if __name__ == "__main__":
    asyncio.run(run_client())
