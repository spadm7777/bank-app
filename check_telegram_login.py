# check_telegram_login.py

from pyrogram import Client

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

app = Client("my_account", api_id=api_id, api_hash=api_hash)

with app:
    me = app.get_me()
    print("✅ 현재 로그인된 계정 정보:")
    print(f"🆔 사용자 ID: {me.id}")
    print(f"👤 유저네임: {me.username}")
    print(f"📞 전화번호: {me.phone_number}")
