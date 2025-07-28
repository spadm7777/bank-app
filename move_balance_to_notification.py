from app import app, db
from models import Transaction

def move_balance_to_notification():
    with app.app_context():
        print("🔧 기존 잔액을 알림잔액으로 이동 중...")
        
        # 모든 거래내역 가져오기
        transactions = Transaction.query.all()
        
        if not transactions:
            print("❌ 거래내역이 없습니다.")
            return
        
        print(f"\n📋 총 {len(transactions)}개의 거래내역을 처리합니다...")
        
        updated_count = 0
        for t in transactions:
            if t.balance is not None and t.notification_balance is None:
                # 기존 balance 값을 notification_balance로 이동
                t.notification_balance = t.balance
                updated_count += 1
                print(f"  📝 ID {t.id}: {t.timestamp.strftime('%Y.%m.%d %H:%M')} {t.type} {t.amount:,}원 → 알림잔액 {t.balance:,}원")
        
        # 변경사항 저장
        db.session.commit()
        
        print(f"\n🎉 완료!")
        print(f"📊 업데이트된 거래: {updated_count}개")
        
        # 결과 확인
        notification_count = Transaction.query.filter(Transaction.notification_balance.isnot(None)).count()
        print(f"📊 알림잔액이 있는 거래: {notification_count}개 / {len(transactions)}개")

if __name__ == "__main__":
    move_balance_to_notification() 