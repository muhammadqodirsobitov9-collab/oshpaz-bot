import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ChatAction
from google import genai

BOT_TOKEN = "8884292329:AAF3Kyd79btdM18HR8JMaK0SFRbqXBtITVU"
GEMINI_API_KEY = "AQ.Ab8RN6K52e8B-P7d-hd_IreowcU0cl-e3n-vO41I0erbiCpW5g"

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = (
    "Siz 'Oshpaz Bola' nomli professional va xushfe'l o'zbek milliy taomlari va jahon oshxonasi mutaxassisisiz. "
    "Foydalanuvchi taqdim etgan masalliqlarga qarab, tayyorlash bosqichlari bilan retsept berishingiz kerak. "
    "Tilingiz ravon va do'stona bo'lsin."
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Men **Oshpaz Bola PRO**man. 👨‍🍳\n\n"
        "Uyda bor masalliqlaringizni yozib yuboring (masalan: *kartoshka, go'sht, piyoz*), "
        "men sizga ulardan qanday mazali taom pishirish mumkinligini aytib beraman!",
        parse_mode="Markdown"
    )

@dp.message(F.text)
async def handle_ingredients(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    try:
        interaction = client.interactions.create(
            model="gemini-3.7-flash",
            input=f"{SYSTEM_PROMPT}\n\nFoydalanuvchi masalliqlari: {message.text}"
        )
        await message.answer(interaction.output_text)
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("⚠️ Kechirasiz, retsept shakllantirishda xatolik bo'ldi. Birozdan so'ng qayta urinib ko'ring.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

