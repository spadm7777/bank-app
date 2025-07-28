
from models import db, User
from flask import Flask
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    user = User(
        username='vworld',
        role='가맹점',
        telegram_group='-1002658267526',
        fee_rate=0.5,
        password_hash=generate_password_hash('vworld123')  # 기본 비번
    )
    db.session.add(user)
    db.session.commit()
    print(f"✅ 사용자 생성 완료: ID={user.id}, 이름={user.username}")
