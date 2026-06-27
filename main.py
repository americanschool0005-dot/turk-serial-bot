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
    waiting_for_name = State()
    waiting_for_season = State()
    waiting_for_episode = State()
    waiting_for_video = State()
    waiting_for_title = State()

# Reply menu
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🎬 Seriallar"))
    return builder.as_markup(resize_keyboard=True)

# Inline series list
def get_series_keyboard():
    builder = InlineKeyboardBuilder()
    series = db.get_all_series()
    for s in series:
        builder.button(text=s["name"], callback_data=f"series:{s['id']}")
    builder.adjust(2)
    return builder.as_markup()

# Command /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    welcome = (
        "Assalomu alaykum! Turk seriallari botiga xush kelibsiz.\n\n"
        "Seriallarni ko'rish uchun quyidagi tugmani bosing."
    )
    if db.is_admin(user_id):
        welcome += (
            "\n\n🛠 *Admin paneli buyruqlari:*\n"
            "• /add\\_series - Yangi serial qismini yuklash\n"
            "• /add\\_admin <user_id> - Yangi admin qo'shish"
        )
    await message.reply(welcome, reply_markup=get_main_menu())

# Handle Reply Button
@dp.message(F.text == "🎬 Seriallar")
async def show_series_menu(message: types.Message):
    await message.reply("Bizdagi turk seriallari ro'yxati:", reply_markup=get_series_keyboard())

# Handle Series Select (Now bypasses season and displays episode buttons directly)
@dp.callback_query(F.data.startswith("series:"))
async def select_series(callback: types.CallbackQuery):
    series_id = int(callback.data.split(":")[1])
    episodes = db.get_all_episodes_for_series(series_id)
    
    series_list = db.get_all_series()
    series_name = next((s["name"] for s in series_list if s["id"] == series_id), "Serial")
    
    if not episodes:
        await callback.message.edit_text(
            f"🎬 *{series_name}* seriali uchun hali qismlar joylanmagan.",
            reply_markup=get_series_keyboard(),
            parse_mode="Markdown"
        )
        return
        
    builder = InlineKeyboardBuilder()
    for ep in episodes:
        # Callback data format: episode:<episode_id>
        builder.button(text=f"{ep['episode_number']}-qism", callback_data=f"episode:{ep['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="back_to_series")
    builder.adjust(4) # 4 columns for clean grid
    
    await callback.message.edit_text(
        f"🎬 *{series_name}* serialining qismini tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Handle Episode Select (Sends the video)
@dp.callback_query(F.data.startswith("episode:"))
async def select_episode(callback: types.CallbackQuery):
    episode_id = int(callback.data.split(":")[1])
    
    row = db.get_episode_by_id(episode_id)
    
    if not row:
        await callback.answer("Qism topilmadi.")
        return
        
    file_id, title, episode_number, series_name = row
    caption = f"🎬 *{series_name}*\n🔑 {episode_number}-qism"
    if title:
        caption += f"\n📌 {title}"
        
    await callback.answer("Video yuborilmoqda...")
    await bot.send_video(chat_id=callback.message.chat.id, video=file_id, caption=caption, parse_mode="Markdown")

# Back to series list
@dp.callback_query(F.data == "back_to_series")
async def back_to_series(callback: types.CallbackQuery):
    await callback.message.edit_text("Bizdagi turk seriallari ro'yxati:", reply_markup=get_series_keyboard())

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
    await state.set_state(AddSeriesStates.waiting_for_episode)
    await callback.message.edit_text(f"🎬 *{series_name}* uchun qism raqamini kiriting:", parse_mode="Markdown")

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
        title=title if title else f"{data['series_name']} {data['episode']}-qism"
    )
    
    if success:
        await message.reply(f"Qism muvaffaqiyatli saqlandi! 🎉\nSerial: {data['series_name']}\nQism: {data['episode']}")
    else:
        await message.reply("Saqlashda xatolik yuz berdi.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
