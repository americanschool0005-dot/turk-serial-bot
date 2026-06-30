import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from dotenv import load_dotenv
import database as db

# Load configs
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN:
    print("XATOLIK: BOT_TOKEN topilmadi!")
    exit(1)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Init DB
db.init_db()
if ADMIN_ID:
    try:
        db.add_admin(int(ADMIN_ID))
    except ValueError:
        pass

# FSM States for Admin upload
class AddSeriesStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_episode = State()
    waiting_for_video = State()
    waiting_for_title = State()

# Localization dictionaries
LOCALIZATION = {
    "uz": {
        "welcome": (
            "✨ *BEST TURKISH DRAMMAS* ✨\n\n"
            "Assalomu alaykum, hurmatli tomoshabin! 👑\n\n"
            "🌐 *Avtomatik til:* Tizim Telegram ilovangiz tilini aniqlab, interfeysni avtomatik ravishda *O'zbekcha* qilib sozlaganini ma'lum qiladi! ⚙️\n\n"
            "Eng sara va mashhur turk seriallari hashamatli olamiga xush kelibsiz. 🍿\n\n"
            "👇 Quyidagi ro'yxatdan o'zingizga ma'qul serialni tanlang:"
        ),
        "series_menu": "✨ *Best Turkish Drammas* seriallari ro'yxati:",
        "select_lang": "👑 *{series_name}* seriali\n\n🌐 Iltimos, tomosha qilish tilini tanlang:",
        "no_episodes": "⚠️ *{series_name}* seriali uchun *{language}* tilida hali qismlar joylanmagan. Boshqa tillardan birini tanlang:",
        "select_episode": "🎬 *{series_name}* ({language} tili)\n\n🍿 Qismni tanlang:",
        "back": "⬅️ Orqaga",
        "btn_series": "🎬 Seriallar",
        "caption_title": "✨ *BEST TURKISH DRAMMAS* ✨",
        "caption_lang": "Til",
        "caption_episode": "qism",
        "caption_name": "Sarlavha",
        "sending_video": "Premium video yuborilmoqda...",
        "btn_other_langs": "🌐 Boshqa tillar",
        "auto_episodes_title": "🎬 *{series_name}* ({language} tili)\n\n🍿 Qismni tanlang:"
    },
    "ru": {
        "welcome": (
            "✨ *BEST TURKISH DRAMMAS* ✨\n\n"
            "Здравствуйте, уважаемый зритель! 👑\n\n"
            "🌐 *Автовыбор языка:* Система определила язык вашего Telegram и автоматически настроила интерфейс на *Русский*! ⚙️\n\n"
            "Добро пожаловать в премиальный мир лучших турецких сериалов. 🍿\n\n"
            "👇 Выберите интересующий вас сериал из списка ниже:"
        ),
        "series_menu": "✨ Список сериалов *Best Turkish Drammas*:",
        "select_lang": "👑 Сериал *{series_name}*\n\n🌐 Пожалуйста, выберите язык просмотра:",
        "no_episodes": "⚠️ Для сериала *{series_name}* еще нет серий на языке: *{language}*. Пожалуйста, выберите другой язык:",
        "select_episode": "🎬 *{series_name}* (Язык: {language})\n\n🍿 Выберите серию:",
        "back": "⬅️ Назад",
        "btn_series": "🎬 Сериалы",
        "caption_title": "✨ *BEST TURKISH DRAMMAS* ✨",
        "caption_lang": "Язык",
        "caption_episode": "серия",
        "caption_name": "Название",
        "sending_video": "Отправка премиум видео...",
        "btn_other_langs": "🌐 Другие языки",
        "auto_episodes_title": "🎬 Сериал *{series_name}* (Язык: {language})\n\n🍿 Выберите серию:"
    },
    "tr": {
        "welcome": (
            "✨ *BEST TURKISH DRAMMAS* ✨\n\n"
            "Merhaba, sevgili seyirci! 👑\n\n"
            "🌐 *Otomatik Dil Seçimi:* Sistem Telegram uygulamanızın dilini tespit etti ve arayüzü otomatik olarak *Türkçe* yaptı! ⚙️\n\n"
            "En iyi ve en popüler Türk dizilerinin lüks dünyasına hoş geldiniz. 🍿\n\n"
            "👇 Lütfen aşağıdaki listeden bir dizi seçin:"
        ),
        "series_menu": "✨ *Best Turkish Drammas* dizi listesi:",
        "select_lang": "👑 *{series_name}* dizisi\n\n🌐 Lütfen izlemek istediğiniz dili seçin:",
        "no_episodes": "⚠️ *{series_name}* dizisi için *{language}* dilinde henüz bölüm yüklenmedi. Lütfen başka bir dil seçin:",
        "select_episode": "🎬 *{series_name}* (Dil: {language})\n\n🍿 Bölüm seçin:",
        "back": "⬅️ Geri",
        "btn_series": "🎬 Diziler",
        "caption_title": "✨ *BEST TURKISH DRAMMAS* ✨",
        "caption_lang": "Dil",
        "caption_episode": "bölüm",
        "caption_name": "Başlık",
        "sending_video": "Premium video gönderiliyor...",
        "btn_other_langs": "🌐 Diğer diller",
        "auto_episodes_title": "🎬 *{series_name}* dizisi (Dil: {language})\n\n🍿 Bölüm seçin:"
    },
    "en": {
        "welcome": (
            "✨ *BEST TURKISH DRAMMAS* ✨\n\n"
            "Welcome, dear viewer! 👑\n\n"
            "🌐 *Language Detection:* The system detected your Telegram language and automatically set the interface to *English*! ⚙️\n\n"
            "Welcome to the premium world of the best Turkish TV series. 🍿\n\n"
            "👇 Select your preferred series from the list below:"
        ),
        "series_menu": "✨ *Best Turkish Drammas* series list:",
        "select_lang": "👑 Series *{series_name}*\n\n🌐 Please select your viewing language:",
        "no_episodes": "⚠️ No episodes loaded in *{language}* for *{series_name}* yet. Please select another language:",
        "select_episode": "🎬 *{series_name}* (Language: {language})\n\n🍿 Select episode:",
        "back": "⬅️ Back",
        "btn_series": "🎬 Series",
        "caption_title": "✨ *BEST TURKISH DRAMMAS* ✨",
        "caption_lang": "Language",
        "caption_episode": "episode",
        "caption_name": "Title",
        "sending_video": "Sending premium video..."
    }
}

def get_lang(user_lang_code: str) -> str:
    if not user_lang_code:
        return "en"
    lang = user_lang_code.lower()
    if lang.startswith("uz"):
        return "uz"
    if lang.startswith("ru"):
        return "ru"
    if lang.startswith("tr"):
        return "tr"
    return "en"

DB_LANG_MAPPING = {
    "uz": "Uzbek",
    "ru": "Russian",
    "tr": "Turkish",
    "en": "English"
}

def get_db_lang(user_lang_code: str) -> str:
    lang = get_lang(user_lang_code)
    return DB_LANG_MAPPING.get(lang, "English")

# Reply menu
def get_main_menu(lang_code: str):
    lang = get_lang(lang_code)
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text=LOCALIZATION[lang]["btn_series"]))
    return builder.as_markup(resize_keyboard=True)

# Inline series list
def get_series_keyboard():
    builder = InlineKeyboardBuilder()
    series = db.get_all_series()
    for s in series:
        builder.button(text=f"✨ {s['name']}", callback_data=f"series:{s['id']}")
    builder.adjust(2)
    return builder.as_markup()

# Command /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(message.from_user.language_code)
    
    # Send the localized bottom reply menu first to register the keyboard
    await message.answer("🍿", reply_markup=get_main_menu(message.from_user.language_code))
    
    welcome = LOCALIZATION[lang]["welcome"]
    if db.is_admin(user_id):
        welcome += (
            "\n\n🛠 *Admin paneli buyruqlari:*\n"
            "• /add\\_series - Yangi serial qismini yuklash\n"
            "• /add\\_admin <user_id> - Yangi admin qo'shish"
        )
    # Send welcome text and show the inline series keyboard directly!
    await message.reply(welcome, reply_markup=get_series_keyboard(), parse_mode="Markdown")

# Handle Reply Button
@dp.message(F.text.in_({"🎬 Seriallar", "🎬 Сериалы", "🎬 Diziler", "🎬 Series"}))
async def show_series_menu(message: types.Message):
    lang = get_lang(message.from_user.language_code)
    await message.reply(LOCALIZATION[lang]["series_menu"], reply_markup=get_series_keyboard(), parse_mode="Markdown")

# Handle Series Select (Now automatically selects the user's interface language by default)
@dp.callback_query(F.data.startswith("series:"))
async def select_series(callback: types.CallbackQuery):
    series_id = int(callback.data.split(":")[1])
    lang = get_lang(callback.from_user.language_code)
    db_lang = get_db_lang(callback.from_user.language_code)
    
    series_list = db.get_all_series()
    series_name = next((s["name"] for s in series_list if s["id"] == series_id), "Serial")
    
    episodes = db.get_all_episodes_for_series(series_id, db_lang)
    if episodes:
        # Display episodes directly in user's language
        builder = InlineKeyboardBuilder()
        for ep in episodes:
            builder.button(text=f"🍿 {ep['episode_number']}-{LOCALIZATION[lang]['caption_episode']}", callback_data=f"episode:{ep['id']}")
        builder.button(text=LOCALIZATION[lang]["btn_other_langs"], callback_data=f"choose_lang:{series_id}")
        builder.button(text=LOCALIZATION[lang]["back"], callback_data="back_to_series")
        builder.adjust(2)
        
        await callback.message.edit_text(
            LOCALIZATION[lang]["auto_episodes_title"].format(series_name=series_name, language=db_lang),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    else:
        # Fallback: No episodes in user's language, prompt them to choose other languages
        builder = InlineKeyboardBuilder()
        languages = [("Turkish 🇹🇷", "Turkish"), ("English 🇬🇧", "English"), ("Russian 🇷🇺", "Russian"), ("Uzbek 🇺🇿", "Uzbek")]
        for text, l in languages:
            builder.button(text=text, callback_data=f"lang:{series_id}:{l}")
        builder.button(text=LOCALIZATION[lang]["back"], callback_data="back_to_series")
        builder.adjust(2)
        
        await callback.message.edit_text(
            LOCALIZATION[lang]["no_episodes"].format(series_name=series_name, language=db_lang),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

# Handle Manual Language Choice Menu
@dp.callback_query(F.data.startswith("choose_lang:"))
async def choose_lang(callback: types.CallbackQuery):
    series_id = int(callback.data.split(":")[1])
    series_list = db.get_all_series()
    series_name = next((s["name"] for s in series_list if s["id"] == series_id), "Serial")
    lang = get_lang(callback.from_user.language_code)
    
    builder = InlineKeyboardBuilder()
    languages = [("Turkish 🇹🇷", "Turkish"), ("English 🇬🇧", "English"), ("Russian 🇷🇺", "Russian"), ("Uzbek 🇺🇿", "Uzbek")]
    for text, l in languages:
        builder.button(text=text, callback_data=f"lang:{series_id}:{l}")
    builder.button(text=LOCALIZATION[lang]["back"], callback_data="back_to_series")
    builder.adjust(2)
    
    await callback.message.edit_text(
        LOCALIZATION[lang]["select_lang"].format(series_name=series_name),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Handle back to manual languages selection
@dp.callback_query(F.data.startswith("back_to_langs:"))
async def back_to_langs(callback: types.CallbackQuery):
    series_id = int(callback.data.split(":")[1])
    series_list = db.get_all_series()
    series_name = next((s["name"] for s in series_list if s["id"] == series_id), "Serial")
    lang = get_lang(callback.from_user.language_code)
    
    builder = InlineKeyboardBuilder()
    languages = [("Turkish 🇹🇷", "Turkish"), ("English 🇬🇧", "English"), ("Russian 🇷🇺", "Russian"), ("Uzbek 🇺🇿", "Uzbek")]
    for text, l in languages:
        builder.button(text=text, callback_data=f"lang:{series_id}:{l}")
    builder.button(text=LOCALIZATION[lang]["back"], callback_data="back_to_series")
    builder.adjust(2)
    
    await callback.message.edit_text(
        LOCALIZATION[lang]["select_lang"].format(series_name=series_name),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Handle Manual Language Select (Displays episodes available in that chosen language)
@dp.callback_query(F.data.startswith("lang:"))
async def select_language(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    series_id = int(parts[1])
    language = parts[2]
    lang = get_lang(callback.from_user.language_code)
    
    episodes = db.get_all_episodes_for_series(series_id, language)
    series_list = db.get_all_series()
    series_name = next((s["name"] for s in series_list if s["id"] == series_id), "Serial")
    
    if not episodes:
        builder = InlineKeyboardBuilder()
        builder.button(text=LOCALIZATION[lang]["back"], callback_data=f"back_to_langs:{series_id}")
        await callback.message.edit_text(
            LOCALIZATION[lang]["no_episodes"].format(series_name=series_name, language=language),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        return
        
    builder = InlineKeyboardBuilder()
    for ep in episodes:
        builder.button(text=f"🍿 {ep['episode_number']}-{LOCALIZATION[lang]['caption_episode']}", callback_data=f"episode:{ep['id']}")
    builder.button(text=LOCALIZATION[lang]["back"], callback_data=f"back_to_langs:{series_id}")
    builder.adjust(2)
    
    await callback.message.edit_text(
        LOCALIZATION[lang]["select_episode"].format(series_name=series_name, language=language),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Handle Episode Select (Sends the video)
@dp.callback_query(F.data.startswith("episode:"))
async def select_episode(callback: types.CallbackQuery):
    episode_id = int(callback.data.split(":")[1])
    lang = get_lang(callback.from_user.language_code)
    
    row = db.get_episode_by_id(episode_id)
    
    if not row:
        await callback.answer("Qism topilmadi.")
        return
        
    file_id, title, episode_number, series_name, language = row
    caption = (
        f"{LOCALIZATION[lang]['caption_title']}\n\n"
        f"🎬 *{series_name}*\n"
        f"🔑 *{episode_number}-{LOCALIZATION[lang]['caption_episode']}*\n"
        f"🌐 *{LOCALIZATION[lang]['caption_lang']}:* {language}"
    )
    if title:
        caption += f"\n📌 *{LOCALIZATION[lang]['caption_name']}:* {title}"
        
    await callback.answer(LOCALIZATION[lang]["sending_video"])
    await bot.send_video(chat_id=callback.message.chat.id, video=file_id, caption=caption, parse_mode="Markdown")

# Back to series list
@dp.callback_query(F.data == "back_to_series")
async def back_to_series(callback: types.CallbackQuery):
    lang = get_lang(callback.from_user.language_code)
    await callback.message.edit_text(LOCALIZATION[lang]["series_menu"], reply_markup=get_series_keyboard(), parse_mode="Markdown")

# --- Admin Handlers ---

@dp.message(Command("add_admin"))
async def add_admin_cmd(message: types.Message):
    if not db.is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Foydalanish: /add_admin <user_id>")
        return
    try:
        new_admin = int(args[1])
        db.add_admin(new_admin)
        await message.reply(f"Foydalanuvchi {new_admin} admin qilindi!")
    except ValueError:
        await message.reply("Xato user_id!")

# Upload series episode FSM
@dp.message(Command("add_series"))
async def add_series_cmd(message: types.Message, state: FSMContext):
    if not db.is_admin(message.from_user.id):
        return
    
    builder = InlineKeyboardBuilder()
    series = db.get_all_series()
    for s in series:
        builder.button(text=s["name"], callback_data=f"add_to:{s['name']}")
    builder.adjust(2)
    
    await message.reply("Qaysi serialga qism qo'shmoqchisiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("add_to:"))
async def process_add_to(callback: types.CallbackQuery, state: FSMContext):
    series_name = callback.data.split(":")[1]
    await state.update_data(series_name=series_name, season=1) # Season defaults to 1
    await state.set_state(AddSeriesStates.waiting_for_language)
    
    # Prompt for language
    builder = InlineKeyboardBuilder()
    languages = ["Turkish", "English", "Russian", "Uzbek"]
    for lang in languages:
        builder.button(text=lang, callback_data=f"add_lang:{lang}")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"🎬 *{series_name}* uchun qaysi tilda qism qo'shmoqchisiz?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("add_lang:"), AddSeriesStates.waiting_for_language)
async def process_add_lang(callback: types.CallbackQuery, state: FSMContext):
    language = callback.data.split(":")[1]
    await state.update_data(language=language)
    await state.set_state(AddSeriesStates.waiting_for_episode)
    await callback.message.edit_text("Qism raqamini kiriting:")

@dp.message(AddSeriesStates.waiting_for_episode)
async def process_episode(message: types.Message, state: FSMContext):
    try:
        episode = int(message.text)
        await state.update_data(episode=episode)
        await state.set_state(AddSeriesStates.waiting_for_video)
        await message.reply("Qism videosini yuboring (fayl yoki video shaklida):")
    except ValueError:
        await message.reply("Faqat raqam kiriting:")

@dp.message(AddSeriesStates.waiting_for_video, F.video | F.document)
async def process_video(message: types.Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AddSeriesStates.waiting_for_title)
    await message.reply("Qism nomini (sarlavhasini) kiriting (yoki /skip yuboring):")

@dp.message(AddSeriesStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    title = "" if message.text == "/skip" else message.text
    data = await state.get_data()
    
    success = db.add_series_episode(
        series_name=data["series_name"],
        season_number=data["season"],
        episode_number=data["episode"],
        file_id=data["file_id"],
        language=data["language"],
        title=title if title else f"{data['series_name']} {data['episode']}-qism"
    )
    
    if success:
        await message.reply(f"Qism muvaffaqiyatli saqlandi! 🎉\nSerial: {data['series_name']}\nTil: {data['language']}\nQism: {data['episode']}")
    else:
        await message.reply("Saqlashda xatolik yuz berdi.")
    await state.clear()

async def main():
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Botni qayta ishga tushirish (Seriallar)")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
