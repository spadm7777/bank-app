# create_table.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base

engine = create_engine('sqlite:///transactions.db', echo=True)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(String(20))
    type = Column(String(10))
    amount = Column(Integer)
    balance = Column(Integer)
    sender = Column(String(50))

Base.metadata.create_all(engine)
print("테이블 생성 완료")