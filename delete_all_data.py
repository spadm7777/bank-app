
from models import db, User, Transaction
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    tx_deleted = Transaction.query.delete()
    user_deleted = User.query.delete()
    db.session.commit()

    print(f"🗑️ 삭제 완료: 사용자 {user_deleted}명, 거래 {tx_deleted}건")
