from pyrogram import Client
import asyncio

api_id = 26558422
api_hash = "4a7d3a6e82ef9319ecbbec94d1c16fc1"

app = Client("my_session", api_id=api_id, api_hash=api_hash)

async def main():
    await app.start()
    print("채팅방 목록 가져오는 중...\n")
    async for dialog in app.get_dialogs():
        print(f"{dialog.chat.title} | {dialog.chat.id}")
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())