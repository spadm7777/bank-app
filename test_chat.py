import asyncio
from pyrogram import Client

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

chat_id = "-1002658267526"  # 문자열로

async def main():
    async with Client("my_account", api_id=api_id, api_hash=api_hash) as app:
        # 1. resolve_peer 테스트
        try:
            peer = await app.resolve_peer(chat_id)
            print("1. resolve_peer 결과:", peer)
        except Exception as e:
            print("1. resolve_peer 에러:", e)

        # 2. 최근 메시지 5개 출력 테스트
        try:
            print("\n2. 최근 메시지 5개:")
            async for msg in app.get_chat_history(chat_id, limit=5):
                print("-", msg.text.replace('\n', ' ') if msg.text else "(텍스트 없음)")
        except Exception as e:
            print("2. get_chat_history 에러:", e)

        # 3. 대화 목록에서 username 출력 (채팅방 정보)
        try:
            print("\n3. 대화 목록에서 username 정보:")
            found = False
            async for d in app.get_dialogs():
                if str(d.chat.id) == chat_id:
                    print(f"채팅명: {d.chat.title}")
                    print(f"ID: {d.chat.id}")
                    print(f"username: {d.chat.username}")
                    found = True
                    break
            if not found:
                print("해당 chat_id를 대화 목록에서 찾을 수 없습니다.")
        except Exception as e:
            print("3. get_dialogs 에러:", e)

if __name__ == "__main__":
    asyncio.run(main())
