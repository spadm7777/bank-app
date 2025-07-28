from sqlalchemy import text
from db import db
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.session.execute(text("ALTER TABLE users ADD COLUMN fee_rate FLOAT DEFAULT 0.5"))
    db.session.commit()
    print("✅ fee_rate 컬럼이 추가되었습니다.")

