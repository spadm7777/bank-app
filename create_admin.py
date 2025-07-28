
from models import db, User
from flask import Flask
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    if User.query.filter_by(username='admin').first():
        print("⚠️ 이미 'admin' 사용자가 존재합니다.")
    else:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='관리자'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ 'admin' 사용자 생성 완료 (비밀번호: admin123)")
