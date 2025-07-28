from app import app, db
from models import Transaction

def check_notification_balance():
    with app.app_context():
        print("🔍 알림잔액 데이터 확인...")
        
        # 모든 거래내역 확인
        transactions = Transaction.query.all()
        
        if not transactions:
            print("❌ 거래내역이 없습니다.")
            return
        
        print(f"\n📋 총 {len(transactions)}개의 거래내역:")
        print("-" * 100)
        print(f"{'ID':<5} {'시간':<20} {'구분':<8} {'금액':<12} {'잔액':<12} {'알림잔액':<12} {'보낸사람'}")
        print("-" * 100)
        
        notification_count = 0
        for t in transactions:
            notification_balance = t.notification_balance if t.notification_balance else '-'
            if t.notification_balance:
                notification_count += 1
            
            print(f"{t.id:<5} "
                  f"{t.timestamp.strftime('%Y.%m.%d %H:%M'):<20} "
                  f"{t.type:<8} "
                  f"{t.amount:,}원{'':<8} "
                  f"{t.balance:,}원{'':<8} "
                  f"{notification_balance:<12} "
                  f"{t.sender}")
        
        print("-" * 100)
        print(f"📊 알림잔액이 있는 거래: {notification_count}개 / {len(transactions)}개")
        
        if notification_count == 0:
            print("\n⚠️ 알림잔액 데이터가 없습니다.")
            print("💡 텔레그램 파싱 스크립트에서 notification_balance 필드를 업데이트해야 합니다.")

if __name__ == "__main__":
    check_notification_balance() 