
from flask import Flask
from models import db, User, Transaction

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def get_ancestors(user):
    ancestors = []
    current = user.parent
    while current:
        ancestors.append(current)
        current = current.parent
    return ancestors

def calculate_and_print_commissions():
    with app.app_context():
        users = User.query.all()
        for user in users:
            if user.role != '매장':
                continue
            print(f"📌 매장: {user.username} (수수료율: {user.fee_rate}%)")
            txs = Transaction.query.filter(Transaction.user_id == user.id, Transaction.type == '입금').all()
            for tx in txs:
                total_amount = tx.amount
                total_fee = user.fee_rate / 100 * total_amount
                remaining_fee = total_fee
                chain = get_ancestors(user)
                print(f"💰 입금: {total_amount}원 → 총 수수료: {int(total_fee)}원")

                for ancestor in chain:
                    rate = ancestor.fee_rate or 0
                    commission = rate / 100 * total_amount
                    print(f" └─ {ancestor.username} 수수료 ({rate}%): {int(commission)}원")
                    remaining_fee -= commission

                print(f" └─ admin 수수료 (남은): {int(remaining_fee)}원\n")

if __name__ == "__main__":
    calculate_and_print_commissions()
