from sqlalchemy import create_engine, text

DB_PATH = 'sqlite:///transactions.db'

engine = create_engine(DB_PATH, echo=False)

with engine.connect() as conn:
    # 테이블 목록 확인
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    print("DB에 있는 테이블 목록:")
    for t in tables:
        print("-", t[0])

    # transactions 테이블 컬럼명 확인
    pragma_result = conn.execute(text("PRAGMA table_info(transactions);")).fetchall()
    print("\ntransactions 테이블 컬럼 정보:")
    for col in pragma_result:
        # col 구조: (cid, name, type, notnull, dflt_value, pk)
        print(f"컬럼명: {col[1]}, 타입: {col[2]}, PK 여부: {col[5]}")
