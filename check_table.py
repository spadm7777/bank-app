from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///db.sqlite3')
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM transactions LIMIT 10"))
    rows = result.fetchall()
    for row in rows:
        print(row)
