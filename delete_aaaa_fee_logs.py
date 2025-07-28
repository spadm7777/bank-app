from app import app, db, FeeLog, User

with app.app_context():
    print('현재 수수료 로그 확인:')
    fee_logs = FeeLog.query.all()
    for log in fee_logs:
        user = User.query.get(log.user_id)
        username = user.username if user else f'Unknown({log.user_id})'
        print(f'ID: {log.id}, User: {username}, Amount: {log.amount}, Description: {log.description[:50]}...')
    
    print('\n삭제할 aaaa 관련 수수료 로그 확인:')
    # aaaa 사용자 ID 찾기 (이미 삭제되었으므로 description에서 확인)
    aaaa_logs = FeeLog.query.filter(FeeLog.description.like('%aaaa%')).all()
    
    if not aaaa_logs:
        # 다른 방법으로 확인
        aaaa_logs = FeeLog.query.filter(FeeLog.description.like('%aaa%')).all()
    
    for log in aaaa_logs:
        user = User.query.get(log.user_id)
        username = user.username if user else f'Unknown({log.user_id})'
        print(f'삭제 예정: ID: {log.id}, User: {username}, Amount: {log.amount}, Description: {log.description}')
    
    if aaaa_logs:
        print(f'\n{len(aaaa_logs)}개의 aaaa 관련 수수료 로그 삭제 중...')
        for log in aaaa_logs:
            db.session.delete(log)
            print(f'삭제됨: ID {log.id} - {log.description[:50]}...')
        
        db.session.commit()
        print('삭제 완료!')
    else:
        print('\n삭제할 aaaa 관련 수수료 로그가 없습니다.')
    
    print('\n삭제 후 수수료 로그 확인:')
    fee_logs = FeeLog.query.all()
    for log in fee_logs:
        user = User.query.get(log.user_id)
        username = user.username if user else f'Unknown({log.user_id})'
        print(f'ID: {log.id}, User: {username}, Amount: {log.amount}, Description: {log.description[:50]}...') 