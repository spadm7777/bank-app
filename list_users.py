
from models import db, User
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    users = User.query.all()
    if not users:
        print("🚫 사용자 없음")
    else:
        for user in users:
            print(f"👤 ID={user.id}, Username={user.username}, Role={user.role}")
