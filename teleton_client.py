from telethon import TelegramClient
from dotenv import load_dotenv
import os
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
client = TelegramClient('session_name', api_id, api_hash)
GROUP_ID = int(os.getenv('GROUP_ID'))

async def search_id(id, client) -> str | Exception:
    await client.get_dialogs()
    print(id)
    entity = await client.get_entity(GROUP_ID)
    try:
        async for msg in client.iter_messages(entity):
            if id in msg.text:
                print(msg.text)
                return msg.text
        return None
    except Exception as e:
        
        return Exception('Ошибка при поиске резюме: ' + str(e))
    


