from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///transactions.db')

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE transactions ADD COLUMN balance INTEGER;"))
        print("balance 컬럼 추가 완료")
    except Exception as e:
        print("컬럼 추가 실패:", e)
