import os
import asyncio
import logging
import urllib.parse
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineQueryResultArticle, InputTextMessageContent
)
import google.generativeai as genai
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884292329:AAGTptmmsveyM-1NFWdy78QOw0fjCjnOjnM")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6K52e8B-P7d-hd_IreowcU0cl-e3n-vO41I0erbiCpW5g")

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
    "Ikkinchi qatordan boshlab o'zbek tilida tayyorlash retseptini juda qisqa va londa formatda berishingiz shart:\n\n"
    "🍲 Taom nomi: ...\n"
    "⏱ Pishirish vaqti: ...\n"
    "👥 Necha kishilik: ...\n"
    "💰 Hamyonbopligi: ...\n"
    "📖 Tayyorlash bosqichlari: (3-4 ta qisqa qadam)\n\n"
    "Javobingiz maksimal 500 belgidan oshmasin."
)

WORLD_RECIPES = [
    {"id": "1", "title": "🍲 O'zbekcha Palov", "desc": "O'zbekiston | Guruch, go'sht, sabzi, piyoz", "text": "🍲 **O'zbekcha Palov**\n\n📌 **Masalliqlar:** Guruch, mol/qo'y go'shti, sabzi, piyoz, yog', zira.\n📖 **Tayyorlanishi:** Qozonda go'sht va piyoz qovuriladi, sabzi solib zirvak qaynatiladi. Guruch solib 25 daqiqa damlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "2", "title": "🥩 Qozon Kabob", "desc": "O'zbekiston | Go'sht, kartoshka, zira", "text": "🥩 **Qozon Kabob**\n\n📌 **Masalliqlar:** Go'sht, kartoshka, yog', tuz, zira.\n📖 **Tayyorlanishi:** Yog'da kartoshka va go'sht qizartirib olinadi va past olovda 45 min dimlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "3", "title": "🥐 Varaqli Somsa", "desc": "O'zbekiston | Un, sariyog', qiyma, piyoz", "text": "🥐 **Varaqli Somsa**\n\n📌 **Masalliqlar:** Un, sariyog', qiyma, piyoz, dumba.\n📖 **Tayyorlanishi:** Xamir yoyilib yog' suriladi, kesib tugiladi va 200°C da pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "4", "title": "🍜 Cho'zma Lag'mon", "desc": "O'zbekiston | Xamir, go'sht, sabzavotlar, sous", "text": "🍜 **Cho'zma Lag'mon**\n\n📌 **Masalliqlar:** Un, tuxum, go'sht, bulg'or qalampiri, pomidor, piyoz, sarimsoq.\n📖 **Tayyorlanishi:** Xamir cho'zilib qaynatiladi. Sabzavot va go'shtdan sersuv sous tayyorlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"}
]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Assalomu alaykum! Men Oshpaz Bola PROman.** 👨‍🍳\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang yoki shunchaki uyingizdagi masalliqlarni yozib yuboring!\n\n"
        "🤖 **Bot:** @oshpaz_bolabot",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.message(F.text == "🏆 Top Retseptlar")
@dp.message(Command("top"))
async def show_top_recipes(message: types.Message):
    top_text = (
        "🏆 **Oshpaz Bola Botining Eng Ommabop Retseptlar Reytingi:**\n\n"
        "🥇 **1-o'rin:** *To'y Osh (O'zbekcha Shaxshona Osh)* — eng ko'p so'ralgan retsept.\n"
        "🥈 **2-o'rin:** *Qozon Kabob* — haqiqiy go'shtxo'rlar tanlovi.\n"
        "🥉 **3-o'rin:** *Klassik Somsa* — har qanday davrada 1-raqamli pishiriq.\n\n"
        "💡 *Ushbu taomlardan birining retseptini olish uchun shunchaki nomini yozib yuboring!*\n\n"
        "🤖 @oshpaz_bolabot"
    )
    await message.answer(top_text, parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(F.text == "📞 Bog'lanish")
@dp.message(Command("contact"))
async def show_contact(message: types.Message):
    contact_text = (
        "📞 **Ma'lumot olish va Bog'lanish**\n\n"
        "Bot bo'yicha takliflar yoki xatoliklar haqida xabar berish uchun adminga murojaat qiling:\n\n"
        "👨‍💻 **Admin:** @sobitovv_o8\n"
        "🤖 **Rasmiy Bot:** @oshpaz_bolabot"
    )
    await message.answer(contact_text, parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(F.text == "🥘 Masalliqlardan taom topish")
async def ask_ingredients(message: types.Message):
    await message.answer("Uyda bor masalliqlaringizni yozib yuboring (masalan: *kartoshka, go'sht, piyoz*):", parse_mode="Markdown")

@dp.message(F.text == "⚡ Tez tayyor bo‘ladigan taomlar")
async def quick_food(message: types.Message):
    await generate_recipe(message, "15-20 daqiqada tayyor bo'ladigan tezkor taom retseptini ber.")

@dp.message(F.text == "💰 Arzon taomlar")
async def cheap_food(message: types.Message):
    await generate_recipe(message, "Hamyonbop arzon masalliqlardan taom retseptini ber.")

@dp.message(F.text == "🍽 Nonushta / Tushlik / Kechki ovqat")
async def meal_times(message: types.Message):
    await generate_recipe(message, "To'yimli taom retseptini ber.")

@dp.message(F.text == "📖 To‘liq retsept")
async def full_recipe(message: types.Message):
    await message.answer("Qaysi taomning to'liq retsepti kerak? Taom nomini yozib yuboring (masalan: *Osh*):", parse_mode="Markdown")

@dp.message(F.text == "🔄 Boshqa taom tavsiya qilish")
async def random_food(message: types.Message):
    await generate_recipe(message, "Kutilmagan, mazali birorta taom tavsiya qil.")

@dp.inline_query()
async def inline_query_handler(query: types.InlineQuery):
    user_query = query.query.strip().lower()
    results = []

    for item in WORLD_RECIPES:
        if not user_query or user_query in item["title"].lower() or user_query in item["desc"].lower():
            results.append(
                InlineQueryResultArticle(
                    id=item["id"],
                    title=item["title"],
                    description=item["desc"],
                    input_message_content=InputTextMessageContent(
                        message_text=item["text"],
                        parse_mode="Markdown"
                    )
                )
            )

    await query.answer(results[:50], cache_time=1)

@dp.message(F.text)
async def handle_user_text(message: types.Message):
    await generate_recipe(message, f"Foydalanuvchi so'rovi: {message.text}")

async def generate_recipe(message: types.Message, prompt_text: str):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(
                f"{SYSTEM_PROMPT}\n\n{prompt_text}",
                generation_config=genai.types.GenerationConfig(max_output_tokens=300)
            )
        )
        full_text = response.text.strip()
        
        lines = full_text.split("\n")
        english_food_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip()
        
        recipe_body += "\n\n🤖 @oshpaz_bolabot"

        encoded_query = urllib.parse.quote(english_food_name)
        image_url = f"https://pollinations.ai/p/{encoded_query}?width=600&height=400&seed=42&nologo=true"

        try:
            await message.answer_photo(
                photo=image_url,
                caption=recipe_body,
                reply_markup=main_keyboard
            )
        except Exception:
            await message.answer(recipe_body, reply_markup=main_keyboard)

    except Exception as e:
        logging.error(f"Gemini xatoligi: {e}")
        await message.answer("⚠️ Kechirasiz, birozdan so'ng qayta urinib ko'ring.\n\n🤖 @oshpaz_bolabot")

async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

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
