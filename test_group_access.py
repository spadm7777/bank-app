from pyrogram import Client

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

# 검사할 chat ID
chat_id = -4867653315

app = Client("my_account", api_id=api_id, api_hash=api_hash)

with app:
    try:
        chat = app.get_chat(chat_id)
        print(f"✅ 그룹 접근 성공: {chat.title}")
    except Exception as e:
        print(f"❌ 접근 실패: {e}")

