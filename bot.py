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
model = genai.GenerativeModel('gemini-2.5-flash')

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

WORLD_RECIPES = [
    # 🇺🇿 O'zbekiston
    {"id": "1", "title": "🍲 O'zbekcha Palov", "desc": "O'zbekiston | Guruch, go'sht, sabzi, piyoz", "text": "🍲 **O'zbekcha Palov**\n\n📌 **Masalliqlar:** Guruch, mol/qo'y go'shti, sabzi, piyoz, yog', zira.\n📖 **Tayyorlanishi:** Qozonda go'sht va piyoz qovuriladi, sabzi solib zirvak qaynatiladi. Guruch solib 25 daqiqa damlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "2", "title": "🥩 Qozon Kabob", "desc": "O'zbekiston | Go'sht, kartoshka, zira", "text": "🥩 **Qozon Kabob**\n\n📌 **Masalliqlar:** Go'sht, kartoshka, yog', tuz, zira.\n📖 **Tayyorlanishi:** Yog'da kartoshka va go'sht qizartirib olinadi va past olovda 45 min dimlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "3", "title": "🥐 Varaqli Somsa", "desc": "O'zbekiston | Un, sariyog', qiyma, piyoz", "text": "🥐 **Varaqli Somsa**\n\n📌 **Masalliqlar:** Un, sariyog', qiyma, piyoz, dumba.\n📖 **Tayyorlanishi:** Xamir yoyilib yog' suriladi, kesib tugiladi va 200°C da pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "4", "title": "🍜 Cho'zma Lag'mon", "desc": "O'zbekiston | Xamir, go'sht, sabzavotlar, sous", "text": "🍜 **Cho'zma Lag'mon**\n\n📌 **Masalliqlar:** Un, tuxum, go'sht, bulg'or qalampiri, pomidor, piyoz, sarimsoq.\n📖 **Tayyorlanishi:** Xamir cho'zilib qaynatiladi. Sabzavot va go'shtdan sersuv sous tayyorlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "5", "title": "🥟 Parda Manti", "desc": "O'zbekiston | Un, go'sht, piyoz, dumba", "text": "🥟 **Parda Manti**\n\n📌 **Masalliqlar:** Un, tuz, to'g'ralgan go'sht, piyoz, dumba.\n📖 **Tayyorlanishi:** Xamir yoyilib tugiladi, mantiqasqonda 45 daqiqa bug'da pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "6", "title": "🥗 Xushxo'r Mastava", "desc": "O'zbekiston | Go'sht, guruch, kartoshka, qatiq", "text": "🥗 **Xushxo'r Mastava**\n\n📌 **Masalliqlar:** Go'sht, guruch, kartoshka, sabzi, piyoz, qatiq.\n📖 **Tayyorlanishi:** Masalliqlar qovurilib bulyon tayyorlanadi. Guruch va kartoshka bilan qaynatiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇮🇹 Italiya
    {"id": "7", "title": "🍕 Pitssa Margarita", "desc": "Italiya | Xamir, pomidor sousi, Motsarella, bazilik", "text": "🍕 **Pitssa Margarita (Italiya)**\n\n📌 **Masalliqlar:** Xamir, pomidor sousi, Motsarella pishlog'i, zaytun yog'i, bazilik.\n📖 **Tayyorlanishi:** Xamir yoyilib sous va pishloq solinadi. 250°C duxovkada 8-10 daqiqa pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "8", "title": "🍝 Spagetti Karbonara", "desc": "Italiya | Spagetti, go'sht, tuxum, Parmesan", "text": "🍝 **Spagetti Karbonara (Italiya)**\n\n📌 **Masalliqlar:** Spagetti, tuxum sariyog'i, Parmesan pishlog'i, mol go'shti, murch.\n📖 **Tayyorlanishi:** Spagetti qaynatiladi. Qovurilgan go'sht va tuxumli sous bilan aralashtiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇯🇵 Yaponiya
    {"id": "9", "title": "🍜 Yapon Rameni", "desc": "Yaponiya | Lapsha, bulyon, tuxum, go'sht, nori", "text": "🍜 **Yapon Rameni (Yaponiya)**\n\n📌 **Masalliqlar:** Ramen lapshasi, bulyon, sooya sousi, tuxum, nori o'ti.\n📖 **Tayyorlanishi:** Quyuq bulyonga pishgan lapsha va qovurilgan masalliqlar solib tortiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "10", "title": "🍣 Sushi-Roll Kaliforniya", "desc": "Yaponiya | Guruch, nori, krab, avokado", "text": "🍣 **Sushi-Roll (Yaponiya)**\n\n📌 **Masalliqlar:** Sushi guruchi, nori yaprog'i, avokado, krab tayoqchalari/losos.\n📖 **Tayyorlanishi:** Nori ustiga guruch va masalliqlar qo'yilib o'raladi hamda bo'laklanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇹🇷 Turkiya
    {"id": "11", "title": "🥙 Iskandar Kebab", "desc": "Turkiya | Döner go'shti, pide non, sariyog', qatiq", "text": "🥙 **Iskandar Kebab (Turkiya)**\n\n📌 **Masalliqlar:** Yupqa go'sht, pide noni, pomidor sousi, sariyog', suzma.\n📖 **Tayyorlanishi:** Non ustiga go'sht, sariyog' va pomidor sousi quyib tortiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},
    {"id": "12", "title": "🥮 Turk Baxlavasi", "desc": "Turkiya | Puxak xamir, yong'oq, sirop", "text": "🥮 **Turk Baxlavasi (Turkiya)**\n\n📌 **Masalliqlar:** Yupqa xamir, sariyog', yong'oq/pista, shakarli sirop.\n📖 **Tayyorlanishi:** Qat-qat xamir duxovkada pishirilib, ustidan issiq sirop quyiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇲🇽 Meksika
    {"id": "13", "title": "🌮 Meksikacha Tako", "desc": "Meksika | Tortilya, qiyma, fasol, sous", "text": "🌮 **Meksikacha Tako (Meksika)**\n\n📌 **Masalliqlar:** Tortilya kulchasi, qiyma go'sht, qizil fasol, Salsa sousi.\n📖 **Tayyorlanishi:** Qovurilgan qiyma va sabzavotlar tortilya ichiga solib tortiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇨🇳 Xitoy
    {"id": "14", "title": "🍗 Pekin O'rdagi", "desc": "Xitoy | O'rdak go'shti, asal, sooya sousi", "text": "🍗 **Pekin O'rdagi (Xitoy)**\n\n📌 **Masalliqlar:** Butun o'rdak, asal, sooya sousi, xitoy ziravorlari.\n📖 **Tayyorlanishi:** O'rdak marinovka qilinib, duxovkada qarsillama qizarguncha pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇮🇳 Hindiston
    {"id": "15", "title": "🍛 Butter Chicken", "desc": "Hindiston | Tovuq go'shti, sariyog', qaymoq, karri", "text": "🍛 **Butter Chicken (Hindiston)**\n\n📌 **Masalliqlar:** Tovuq filosi, pomidor sousi, sariyog', qaymoq, karri ziravori.\n📖 **Tayyorlanishi:** Ziravorli tovuq qovurilib, sariyog'li pomidor sousida dimlanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇺🇸 AQSH
    {"id": "16", "title": "🍔 Klassik Cheeseburger", "desc": "AQSH | Burger noni, kotleta, pishloq", "text": "🍔 **Klassik Cheeseburger (AQSH)**\n\n📌 **Masalliqlar:** Burger noni, mol go'shtidan kotleta, Chedder pishlog'i, sabzavotlar.\n📖 **Tayyorlanishi:** Kotleta qovurilib, nonlar orasiga sous va sabzavotlar bilan joylanadi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇫🇷 Fransiya
    {"id": "17", "title": "🍲 Ratatuy", "desc": "Fransiya | Baqlajon, kabachki, pomidor", "text": "🍲 **Ratatuy (Fransiya)**\n\n📌 **Masalliqlar:** Baqlajon, kabachki, pomidor, bulg'or qalampiri, rozmarin.\n📖 **Tayyorlanishi:** Sabzavotlar doira shaklida kesilib, sous ustiga teriladi va duxovkada pishiriladi.\n\n🤖 **Bot:** @oshpaz_bolabot"},

    # 🇰🇷 Janubiy Koreya
    {"id": "18", "title": "🥘 Kimchi Chjige", "desc": "Koreya | Kimchi, tofu pishlog'i, go'sht", "text": "🥘 **Kimchi Chjige (Koreya)**\n\n📌 **Masalliqlar:** Kimchi karomi, tofu, mol go'shti, sarimsoq, yashil piyoz.\n📖 **Tayyorlanishi:** Kimchi va go'sht qovurilib, bulyon quyiladi va tofu solib qaynatiladi.\n\n🤖 **Bot:** @oshpaz_bolabot"}
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
    await generate_recipe(message, f"Foydalanuvchi masalliqlari yoki so'rovi: {message.text}")

async def generate_recipe(message: types.Message, prompt_text: str):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(f"{SYSTEM_PROMPT}\n\n{prompt_text}")
        )
        full_text = response.text.strip()
        
        lines = full_text.split("\n")
        english_food_name = lines[0].strip()
        recipe_body = "\n".join(lines[1:]).strip()
        
        # Bot niki qo'shish
        recipe_body += "\n\n🤖 @oshpaz_bolabot"

        if len(recipe_body) > 1000:
            recipe_body = recipe_body[:975] + "...\n\n🤖 @oshpaz_bolabot"

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
        await message.answer("⚠️ Kechirasiz, retsept shakllantirishda xatolik bo'ldi. Birozdan so'ng qayta urinib ko'ring.\n\n🤖 @oshpaz_bolabot")

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
