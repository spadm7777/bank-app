from pyrogram import Client

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

app = Client("my_account", api_id=api_id, api_hash=api_hash)

with app:
    print("✅ 현재 계정이 참여 중인 그룹 목록:\n")
    for dialog in app.get_dialogs():
        chat = dialog.chat
        if chat.type in ["group", "supergroup"]:
            print(f"{chat.title} → Chat ID: {chat.id}")
