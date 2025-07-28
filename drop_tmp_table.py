import sqlite3

DB_PATH = 'your_database_file.sqlite3'  # 실제 DB 파일명으로 변경하세요

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS _alembic_tmp_users;")
conn.commit()
conn.close()

print("임시 테이블 _alembic_tmp_users 삭제 완료")
