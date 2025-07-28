
from models import db, User
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    all_users = User.query.all()
    for user in all_users:
        print(f"🗑️ 삭제 대상: {user.username} (ID={user.id})")
        db.session.delete(user)
    db.session.commit()
    print(f"✅ 모든 사용자 삭제 완료: {len(all_users)}명")
