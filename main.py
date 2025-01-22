import os
import asyncio
import mysql.connector
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import logging

# Telegram bot token
TELEGRAM_TOKEN = "7404596976:AAGRG0-P1R2cXRW9tDTHDTgZKoDoOZI9xbQ"
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# MySQL konfiguratsiyasi
db_config = {
    'host': '45.92.173.29',
    'user': 'sql_1_free',
    'password': 'asliddin2909',
    'database': 'sql_1_free'
}

# MySQL ulanishi
def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"MySQL ulanish xatosi: {err}")
        return None

# Top o'yinchilarni olish funksiyasi
def get_top_players(limit=10):
    connection = None
    try:
        connection = create_db_connection()
        if connection is None:
            return None

        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT nick, deaths, frags
        FROM csstats_players
        ORDER BY frags DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))
        top_players = cursor.fetchall()
        return top_players
    except mysql.connector.Error as err:
        logging.error(f"Ma'lumotni olishda xato: {err}")
        return None
    finally:
        if connection:
            connection.close()

# /top komanda uchun handler
@dp.message_handler(commands=['top'])
async def send_top_players(message: types.Message):
    limit = 10  # Standart limit
    try:
        if len(message.text.split()) > 1:
            limit = int(message.text.split()[1])
            if limit > 50:  # Maksimal limit
                limit = 50
    except ValueError:
        await message.answer("⚠️ Limitni to'g'ri kiriting. Masalan: `/top 15`", parse_mode="Markdown")
        return

    top_players = get_top_players(limit)
    if top_players:
        response_message = (
            "TOP O'YINCHILAR:\n"
            "==========================================\n"
            "№   Nick✍️       | Kill🛡      | Death💀   \n"
            "==========================================\n"
        )
        for idx, player in enumerate(top_players, 1):
            player_name = (player['nick'][:10] + '…') if len(player['nick']) > 10 else player['nick']
            response_message += f"{idx:<2} {player_name:<10}    | {player['frags']:<11} | {player['deaths']:<10}\n"
        response_message += "================================================"
        await message.answer(f"```{response_message}```", parse_mode="Markdown")
    else:
        await message.answer("Top o'yinchilarni olishda xato yuz berdi yoki ma'lumot yo'q.")

# Yangi banlarni tekshirish funksiyasi
async def check_new_bans():
    last_checked_time = None  # Oxirgi tekshirilgan vaqtni saqlaydi

    while True:
        try:
            with mysql.connector.connect(**db_config) as connection:
                cursor = connection.cursor(dictionary=True)

                if last_checked_time is None:
                    cursor.execute("SELECT * FROM amx_bans ORDER BY ban_created DESC LIMIT 1")
                    last_checked_ban = cursor.fetchone()
                    last_checked_time = last_checked_ban['ban_created'] if last_checked_ban else None
                
                query = "SELECT * FROM amx_bans WHERE ban_created > %s ORDER BY ban_created DESC"
                cursor.execute(query, (last_checked_time,))
                new_bans = cursor.fetchall()

                for ban in new_bans:
                    message = (
                        f"🔒 Yangi ban topildi!\n"
                        f"👤 O'yinchi: {ban['player_nick']}\n"
                        f"🎮 O'yinchi ID: {ban['player_id']}\n"
                        f"🚫 Ban sababi: {ban['ban_reason']}\n"
                        f"👮‍♂️ Admin: {ban['admin_nick']}\n"
                        f"🕒 Ban vaqti: {ban['ban_created']}\n"
                        f"⏳ Ban muddati: {ban['ban_length']} daqiqa\n"
                        f"🔍 Server: {ban['server_name']}\n"
                    )
                    map_name = ban['map_name']
                    map_image_path = os.path.join("maps", f"{map_name}.jpg")
                    
                    if os.path.exists(map_image_path):
                        with open(map_image_path, 'rb') as photo:
                            await bot.send_photo(chat_id="-1002285396062", photo=photo, caption=message)
                    else:
                        await bot.send_message(chat_id="-1002285396062", text=message)

                if new_bans:
                    last_checked_time = new_bans[0]['ban_created']

        except mysql.connector.Error as err:
            logging.error(f"Baza xatosi: {err}")
        except Exception as e:
            logging.error(f"Noma'lum xato: {e}")

        await asyncio.sleep(60)

# Botni ishga tushirish
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_bans())
    executor.start_polling(dp, skip_updates=True)
