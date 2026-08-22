import os
import asyncio
import logging
import urllib.parse
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from google import genai
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884292329:AAF3Kyd79btdM18HR8JMaK0SFRbqXBtITVU")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6K52e8B-P7d-hd_IreowcU0cl-e3n-vO41I0erbiCpW5g")

# Client va Bot obyektlari
client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🥘 Masalliqlardan taom topish"), KeyboardButton(text="⚡ Tez tayyor bo‘ladigan taomlar")],
        [KeyboardButton(text="💰 Arzon taomlar"), KeyboardButton(text="🍽 Nonushta / Tushlik / Kechki ovqat")],
        [KeyboardButton(text="📖 To‘liq retsept"), KeyboardButton(text="🔄 Boshqa taom tavsiya qilish")]
    ],
    resize_keyboard=True
)

SYSTEM_PROMPT = (
    "Siz 'Oshpaz Bola' nomli professional o'zbek milliy va jahon oshxonasi mutaxassisisiz. "
    "Javobingizning eng birinchi qatoriga faqat taomning qisqa inglizcha nomini yozing (masalan: Uzbek pilaf, Beef soup). "
    "Ikkinchi qatordan boshlab o'zbek tilida tayyorlash retseptini qisqa va lochin formatda berishingiz shart:\n\n"
    "🍲 Taom nomi: ...\n"
    "⏱ Pishirish vaqti: ...\n"
    "👥 Necha kishilik: ...\n"
    "💰 Hamyonbopligi: ...\n"
    "📖 Tayyorlash bosqichlari: (qisqa va tushunarli)\n\n"
    "Javobingiz umumiy uzunligi 800 ta belgidan oshmasin."
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Assalomu alaykum! Men Oshpaz Bola PROman.** 👨‍🍳\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang yoki shunchaki uyingizdagi masalliqlarni yozib yuboring!",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.message(F.text == "🥘 Masalliqlardan taom topish")
async def ask_ingredients(message: types.Message):
    await message.answer("Uyda bor masalliqlaringizni yozib yuboring (masalan: *kartoshka, go'sht, piyoz*):", parse_mode="Markdown")

@dp.message(F.text == "⚡ Tez tayyor bo‘ladigan taomlar")
async def quick_food(message: types.Message):
    await generate_recipe(message, "15-20 daqiqada tayyor bo'ladigan tezkor va mazali taom retseptini ber.")

@dp.message(F.text == "💰 Arzon taomlar")
async def cheap_food(message: types.Message):
    await generate_recipe(message, "Hamyonbop byudjet uchun arzon masalliqlardan tayyorlanadigan taom retseptini ber.")

@dp.message(F.text == "🍽 Nonushta / Tushlik / Kechki ovqat")
async def meal_times(message: types.Message):
    await generate_recipe(message, "Kun davomida tayyorlash mumkin bo'lgan to'yimli va mazali taom retseptini ber.")

@dp.message(F.text == "📖 To‘liq retsept")
async def full_recipe(message: types.Message):
    await message.answer("Qaysi taomning to'liq retsepti kerak? Taom nomini yozib yuboring (masalan: *Osh*, *Somsa*):", parse_mode="Markdown")

@dp.message(F.text == "🔄 Boshqa taom tavsiya qilish")
async def random_food(message: types.Message):
    await generate_recipe(message, "Kutilmagan, mazali birorta taom retseptini tavsiya qil.")

@dp.message(F.text)
async def handle_user_text(message: types.Message):
    await generate_recipe(message, f"Foydalanuvchi masalliqlari: {message.text}")

async def generate_recipe(message: types.Message, prompt_text: str):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\n{prompt_text}"
        )
        full_text = response.text.strip()
        
        lines = full_text.split("\n")
        english_food_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip()
        
        # Caption uzilib qolmasligi uchun 1000 belgiga qisqartiramiz
        if len(recipe_body) > 1000:
            recipe_body = recipe_body[:995] + "..."

        encoded_query = urllib.parse.quote(english_food_name)
        image_url = f"https://pollinations.ai/p/{encoded_query}?width=800&height=600&seed=42&nologo=true"

        try:
            await message.answer_photo(
                photo=image_url,
                caption=recipe_body,
                reply_markup=main_keyboard
            )
        except Exception as img_err:
            logging.error(f"Rasm yuborishda xatolik: {img_err}")
            await message.answer(recipe_body, reply_markup=main_keyboard)

    except Exception as e:
        logging.error(f"Gemini xatoligi: {e}")
        await message.answer("⚠️ Kechirasiz, retsept shakllantirishda xatolik bo'ldi. Birozdan so'ng qayta urinib ko'ring.")

async def handle(request):
    return web.Response(text="Bot 24/7 ishlamoqda!")

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
