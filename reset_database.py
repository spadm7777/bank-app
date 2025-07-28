
from models import db, User, Transaction
from flask import Flask
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # DB 파일 삭제
    if os.path.exists('bank.db'):
        os.remove('bank.db')
        print("📛 기존 DB 삭제 완료")

    # 테이블 재생성
    db.create_all()
    print("✅ 테이블 재생성 완료")
