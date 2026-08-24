import os
import asyncio
import logging
import urllib.parse
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import google.generativeai as genai
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🥘 Masalliqlardan taom topish"), KeyboardButton(text="⚡ Tez tayyor bo‘ladigan taomlar")],
        [KeyboardButton(text="💰 Arzon taomlar"), KeyboardButton(text="🍽 Nonushta / Tushlik / Kechki ovqat")],
        [KeyboardButton(text="🏆 Top Retseptlar"), KeyboardButton(text="📞 Bog'lanish")],
        [KeyboardButton(text="📖 To‘liq retsept"), KeyboardButton(text="🔄 Boshqa taom tavsiya qilish")]
    ],
    resize_keyboard=True
)

SYSTEM_PROMPT = (
    "Siz 'Oshpaz Bola' nomli professional o'zbek milliy va jahon oshxonasi mutaxassisisiz. "
    "Javobingizning eng birinchi qatoriga faqat taomning qisqa inglizcha nomini yozing (masalan: Uzbek pilaf). "
    "Ikkinchi qatordan boshlab o'zbek tilida tayyorlash retseptini juda qisqa formatda berishingiz shart:\n\n"
    "Taom nomi: ...\n"
    "Pishirish vaqti: ...\n"
    "Necha kishilik: ...\n"
    "Hamyonbopligi: ...\n"
    "Tayyorlash bosqichlari: (3-4 ta qisqa qadam)\n\n"
    "Javobingiz maksimal 400 belgidan oshmasin va hech qanday special belgilar ishlatmang."
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Men Oshpaz Bola PROman. 👨‍🍳\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang yoki shunchaki uyingizdagi masalliqlarni yozib yuboring!\n\n"
        "🤖 Bot: @oshpaz_bolabot",
        reply_markup=main_keyboard
    )

@dp.message(F.text == "🏆 Top Retseptlar")
async def show_top_recipes(message: types.Message):
    await message.answer("🏆 Top Retseptlar:\n1. To'y Osh\n2. Qozon Kabob\n3. Somsa\n\n🤖 @oshpaz_bolabot", reply_markup=main_keyboard)

@dp.message(F.text == "📞 Bog'lanish")
async def show_contact(message: types.Message):
    await message.answer("👨‍💻 Admin: @sobitovv_o8\n🤖 Bot: @oshpaz_bolabot", reply_markup=main_keyboard)

@dp.message(F.text)
async def handle_user_text(message: types.Message):
    await generate_recipe(message, message.text)

async def generate_recipe(message: types.Message, user_input: str):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(f"{SYSTEM_PROMPT}\n\nFoydalanuvchi so'rovi: {user_input}")
        )
        full_text = response.text.strip()
        lines = full_text.split("\n")
        english_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip() + "\n\n🤖 @oshpaz_bolabot"

        encoded_query = urllib.parse.quote(english_name)
        image_url = f"https://pollinations.ai/p/{encoded_query}?width=600&height=400&seed=42&nologo=true"

        try:
            await message.answer_photo(photo=image_url, caption=recipe_body, reply_markup=main_keyboard)
        except Exception:
            await message.answer(recipe_body, reply_markup=main_keyboard)
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("⚠️ Kechirasiz, birozdan so'ng qayta urinib ko'ring.\n\n🤖 @oshpaz_bolabot")

async def handle(request):
    return web.Response(text="Bot Live!")

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
