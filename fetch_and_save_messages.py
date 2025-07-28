async def fetch_and_save_messages():
    session = Session()
    chat_id = -1002658267526  # 실제 ID로 교체
    async for msg in app.get_chat_history(chat_id, limit=100):
        if not msg.text:
            continue
        print("메시지 받음:", msg.text[:50].replace('\n', ' ') + "...")
        data = parse_message(msg.text, msg.date)
        if data:
            exists = session.query(Transaction).filter_by(
                timestamp=data['timestamp'],
                type=data['type'],
                amount=data['amount'],
                balance=data['balance'],
                sender=data['sender']
            ).first()
            if not exists:
                session.add(Transaction(**data))
                print("저장:", data)
            else:
                print("중복 메시지로 저장 생략")
        else:
            print("파싱 실패:", msg.text)
    session.commit()
    session.close()
    print("DB 커밋 완료")
