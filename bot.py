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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884292329:AAF3Kyd79btdM18HR8JMaK0SFRbqXBtITVU")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6K52e8B-P7d-hd_IreowcU0cl-e3n-vO41I0erbiCpW5g")

# Gemini sozlashi
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
    "Javobingizning eng birinchi qatoriga faqat taomning qisqa inglizcha nomini yozing (masalan: Uzbek pilaf, Beef soup). "
    "Ikkinchi qatordan boshlab o'zbek tilida tayyorlash retseptini qisqa va londa formatda berishingiz shart:\n\n"
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

@dp.message(F.text == "🏆 Top Retseptlar")
@dp.message(Command("top"))
async def show_top_recipes(message: types.Message):
    top_text = (
        "🏆 **Oshpaz Bola Botining Eng Ommabop Retseptlar Reytingi:**\n\n"
        "🥇 **1-o'rin:** *To'y Osh (O'zbekcha Shaxshona Osh)* — eng ko'p so'ralgan va sevimli taom.\n"
        "🥈 **2-o'rin:** *Qozon Kabob* — haqiqiy go'shtxo'rlar tanlovi.\n"
        "🥉 **3-o'rin:** *Klassik Somsa* — har qanday davrada 1-raqamli pishiriq.\n\n"
        "💡 *Ushbu taomlardan birining retseptini olish uchun shunchaki nomini yozib yuboring!*"
    )
    await message.answer(top_text, parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(F.text == "📞 Bog'lanish")
@dp.message(Command("contact"))
async def show_contact(message: types.Message):
    contact_text = (
        "📞 **Ma'lumot olish va Bog'lanish**\n\n"
        "Bot bo'yicha takliflar, hamkorlik yoki xatoliklar haqida xabar berish uchun adminga murojaat qilishingiz mumkin:\n\n"
        "👨‍💻 **Admin:** @sobitovv_o8\n"
        "🤖 **Bot versiyasi:** Oshpaz Bola PRO v2.5 AI\n"
        "✨ Qulay va mazali retseptlar ulashishda davom etamiz!"
    )
    await message.answer(contact_text, parse_mode="Markdown", reply_markup=main_keyboard)

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
        # Gemini generatsiyasi
        response = await asyncio.to_thread(
            model.generate_content,
            f"{SYSTEM_PROMPT}\n\n{prompt_text}"
        )
        full_text = response.text.strip()
        
        lines = full_text.split("\n")
        english_food_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip()
        
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
