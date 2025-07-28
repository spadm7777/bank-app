
import asyncio
from pyrogram import Client

api_id = 123456      # 🔁 본인의 API ID로 교체
api_hash = "your_api_hash"  # 🔁 본인의 API HASH로 교체
session_name = "vworld_session"

async def main():
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
        async for dialog in app.get_dialogs():
            chat = dialog.chat
            print(f"📢 이름: {chat.title or chat.first_name}")
            print(f"🆔 ID: {chat.id}")
            print(f"👥 타입: {chat.type}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
