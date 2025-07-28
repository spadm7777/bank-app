from app import app, db, Transaction

with app.app_context():
    transactions = Transaction.query.limit(5).all()
    if not transactions:
        print("DB에 저장된 거래 내역이 없습니다.")
    else:
        for t in transactions:
            print(f"ID: {t.id}, 구분: {t.type}, 금액: {t.amount}, 보낸사람: {t.sender}")
