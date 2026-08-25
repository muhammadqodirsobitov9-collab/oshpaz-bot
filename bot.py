import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import google.generativeai as genai
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY.strip())

# Har qanday 404 xatosini oldini oluvchi avto-model tanlash
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    selected_model = available_models[0] if available_models else 'models/gemini-1.5-flash'
except Exception:
    selected_model = 'models/gemini-1.5-flash'

model = genai.GenerativeModel(selected_model)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🥘 Masalliqlardan taom topish"), KeyboardButton(text="⚡ Tez tayyor bo‘ladigan taomlar")],
        [KeyboardButton(text="💰 Arzon taomlar"), KeyboardButton(text="🍽 Nonushta / Tushlik / Kechki ovqat")],
        [KeyboardButton(text="🏆 Top Retseptlar"), KeyboardButton(text="📞 Bog'lanish")]
    ],
    resize_keyboard=True
)

SYSTEM_PROMPT = (
    "Siz 'Oshpaz Bola' nomli professional o'zbek oshxonasi mutaxassisisiz. "
    "Foydalanuvchi so'roviga mos o'zbek tilida juda qisqa retsept berishingiz shart:\n\n"
    "Taom nomi: ...\n"
    "Pishirish vaqti: ...\n"
    "Necha kishilik: ...\n"
    "Tayyorlash bosqichlari: (3-4 ta qisqa qadam)\n\n"
    "Javobingiz maksimal 400 belgidan oshmasin va formatlash belgilaridan foydalanmang."
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
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(f"{SYSTEM_PROMPT}\n\nFoydalanuvchi so'rovi: {message.text}")
        )
        recipe_text = response.text.strip() + "\n\n🤖 @oshpaz_bolabot"
        await message.answer(recipe_text, reply_markup=main_keyboard)
    except Exception as e:
        logging.error(f"Gemini Xatosi: {e}")
        await message.answer(
            f"⚠️ API Xatolik: {str(e)[:80]}\n\n"
            "📩 Adminga yuboring: @sobitovv_o8\n\n"
            "🤖 @oshpaz_bolabot", 
            reply_markup=main_keyboard
        )

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
    
