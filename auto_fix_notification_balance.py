from app import app, db
from models import Transaction
import time
import schedule
from datetime import datetime

def auto_fix_notification_balance():
    """알림잔액이 None인 거래들을 자동으로 수정"""
    with app.app_context():
        try:
            # 알림잔액이 None인 거래들 찾기
            none_transactions = Transaction.query.filter(
                Transaction.notification_balance.is_(None)
            ).all()
            
            if none_transactions:
                print(f"🔧 {datetime.now().strftime('%H:%M:%S')} - {len(none_transactions)}개 거래 알림잔액 수정 중...")
                
                updated_count = 0
                for t in none_transactions:
                    if t.balance is not None:
                        t.notification_balance = t.balance
                        updated_count += 1
                
                if updated_count > 0:
                    db.session.commit()
                    print(f"✅ {updated_count}개 거래 알림잔액 수정 완료")
                else:
                    print("ℹ️ 수정할 거래 없음")
            else:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - 모든 거래 알림잔액 정상")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

def main():
    print("🤖 알림잔액 자동 수정 스케줄러 시작...")
    print("⏰ 10초마다 실행됩니다.")
    print("⏹️ Ctrl+C로 중지")
    
    # 10초마다 실행
    schedule.every(10).seconds.do(auto_fix_notification_balance)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ 스케줄러 중지됨")

if __name__ == "__main__":
    main() 