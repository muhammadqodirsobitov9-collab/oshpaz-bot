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

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bosh menyu tugmalari
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
    "Javobingizning eng birinchi qatoriga faqat taomning qisqa inglizcha nomini yozing (masalan: Uzbek pilaf, Beef soup, Fried potatoes). "
    "Ikkinchi qatordan boshlab o'zbek tilida quyidagi formatda retsept berishingiz shart:\n\n"
    "🍲 Taom nomi: ...\n"
    "⏱ Pishirish vaqti: ...\n"
    "👥 Necha kishilik: ...\n"
    "💰 Hamyonbopligi: ...\n"
    "📖 Tayyorlash bosqichlari: ...\n"
    "Tilingiz ravon, do'stona va emojilarga boy bo'lsin."
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
    await generate_recipe(message, "15-20 daqiqada tayyor bo'ladigan juda tezkor va mazali taom retseptini ber.")

@dp.message(F.text == "💰 Arzon taomlar")
async def cheap_food(message: types.Message):
    await generate_recipe(message, "Talabalar va hamyonbop byudjet uchun arzon masalliqlardan tayyorlanadigan taom retseptini ber.")

@dp.message(F.text == "🍽 Nonushta / Tushlik / Kechki ovqat")
async def meal_times(message: types.Message):
    await generate_recipe(message, "Kun davomida tayyorlash mumkin bo'lgan to'yimli va mazali taom g'oyasi va retseptini ber.")

@dp.message(F.text == "📖 To‘liq retsept")
async def full_recipe(message: types.Message):
    await message.answer("Qaysi taomning to'liq retsepti kerak? Taom nomini yozib yuboring (masalan: *Osh*, *Somsa*, *Manti*):", parse_mode="Markdown")

@dp.message(F.text == "🔄 Boshqa taom tavsiya qilish")
async def random_food(message: types.Message):
    await generate_recipe(message, "Kutilmagan, mazali va ajoyib birorta milliy yoki jahon taomi retseptini tavsiya qil.")

@dp.message(F.text)
async def handle_user_text(message: types.Message):
    await generate_recipe(message, f"Foydalanuvchi so'rovi yoki masalliqlari: {message.text}")

async def generate_recipe(message: types.Message, prompt_text: str):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    try:
        interaction = client.interactions.create(
            model="gemini-2.5-flash",
            input=f"{SYSTEM_PROMPT}\n\n{prompt_text}"
        )
        full_text = interaction.output_text.strip()
        
        # Inglizcha taom nomini ajratib olish (rasm qidirish uchun)
        lines = full_text.split("\n")
        english_food_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip()
        
        # Yuqori sifatli rasm havolasini shakllantirish
        encoded_query = urllib.parse.quote(english_food_name)
        image_url = f"https://pollinations.ai/p/{encoded_query}?width=800&height=600&seed=42&nologo=true"

        # Rasm va retseptni birga yuborish
        await message.answer_photo(
            photo=image_url,
            caption=recipe_body,
            reply_markup=main_keyboard
        )

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        # Agar rasm yuklashda muammo bo'lsa, faqat matnning o'zini yuboradi
        try:
            await message.answer(full_text, reply_markup=main_keyboard)
        except:
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
