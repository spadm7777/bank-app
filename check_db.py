# check_db.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine('sqlite:///transactions.db', echo=False)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    type = Column(String(10))
    amount = Column(Integer)
    balance = Column(Integer)
    sender = Column(String(50))

Session = sessionmaker(bind=engine)
session = Session()

transactions = session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(20).all()

print(f"DB 'transactions.db'에서 최근 20개 데이터:")
for t in transactions:
    print(t.id, t.timestamp.strftime('%Y-%m-%d %H:%M:%S'), t.type, t.amount, t.balance, t.sender)