import math
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()  # local .env faylidan o'qiydi (Railway'da environment variables ishlatiladi)
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from utils import generate_receipt_image

# --- SOZLAMALAR ---
API_TOKEN = os.getenv('BOT_TOKEN', '8797944374:AAE7xuw_RR5bhLIrFOxAYxXhy9HGB_cMBc8')
ADMIN_ID = 5094694146

PRICES_FILE = 'prices.json'
USERS_FILE = 'users.json'
BANNED_FILE = 'banned.json'
ORDERS_FILE = 'orders.json'

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_order(order_data: dict):
    orders = load_orders()
    orders.append(order_data)
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user(user: types.User):
    users = load_users()
    users[str(user.id)] = {
        'id': user.id,
        'ism': user.full_name,
        'username': f'@{user.username}' if user.username else 'Yo\'q',
        'sana': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_banned():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def is_banned(user_id: int) -> bool:
    return str(user_id) in [str(i) for i in load_banned()]

def ban_user(user_id: int):
    banned = load_banned()
    if str(user_id) not in [str(i) for i in banned]:
        banned.append(user_id)
        with open(BANNED_FILE, 'w') as f:
            json.dump(banned, f)

def unban_user(user_id: int):
    banned = [i for i in load_banned() if str(i) != str(user_id)]
    with open(BANNED_FILE, 'w') as f:
        json.dump(banned, f)

DEFAULT_PRICES = {
    "zashitka": 22000.0,
    "tikuv": 40000.0,
    "karsaj": 5000.0,
    "karset": 12000.0,
    "radnoy_kalso": 7000.0,
    "oddiy_kalso": 3000.0,
    "lang": "uz"
}

def load_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure numeric values are floats
            for k, v in data.items():
                if k != 'lang' and isinstance(v, (int, float, str)):
                    try: data[k] = float(v)
                    except: pass
            return data
    return DEFAULT_PRICES.copy()

def save_prices(prices):
    with open(PRICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=4)

PRICES = load_prices()

def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Mahsulotlar Hisoboti")],
            [KeyboardButton(text="⚙️ Narxlar va Sozlamalar"), KeyboardButton(text="👥 Foydalanuvchilar")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin menyusi"
    )

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class OrderProcess(StatesGroup):
    waiting_lang = State()
    waiting_name = State()
    waiting_room_name = State()
    waiting_dims = State()
    waiting_skladka = State()
    waiting_components = State()
    waiting_tyul_narxi = State()
    waiting_parter_narxi = State()
    waiting_style = State()
    waiting_kalso = State()
    waiting_next_action = State()

class SettingsProcess(StatesGroup):
    waiting_for_price = State()

# --- 1. START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if is_banned(message.from_user.id):
        await message.answer("⛔ Siz bu botdan foydalanish imkoniyatingizdan mahrum qilindingiz.")
        return
    
    user = message.from_user
    save_user(user)
    
    if user.id != ADMIN_ID:
        uname = f'@{user.username}' if user.username else 'Yo\'q'
        notif = f"👤 Yangi foydalanuvchi botga kirdi!\n\n🪪 Ism: {user.full_name}\n🔗 Username: {uname}\n🆔 ID: {user.id}"
        try: await bot.send_message(ADMIN_ID, notif)
        except: pass
    
    lang = PRICES.get('lang', 'uz')
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔵 Telegram", url="https://t.me/rayyonpardalar"),
                types.InlineKeyboardButton(text="📸 Instagram", url="https://www.instagram.com/rayyon_pardalar?igsh=ZDM4ZDU5NDczcmNw")
            ],
            [types.InlineKeyboardButton(text="✂️ Hisoblashni boshlash", callback_data="start_calc")]
        ]
    )
    
    if lang == 'uz':
        msg = (
            "👋 **Rayyon Pardalar** hisob-kitob tizimiga xush kelibsiz!\n\n"
            "Bizning ijtimoiy tarmoqlarimiz:\n"
            "🔹 [Telegram](https://t.me/rayyonpardalar)\n"
            "🔸 [Instagram](https://www.instagram.com/rayyon_pardalar)\n\n"
            "Hisoblashni boshlash uchun quyidagi tugmani bosing yoki mijoz ismini yozib yuboring:"
        )
    else:
        msg = (
            "👋 Добро пожаловать в систему расчета **Rayyon Pardalar**!\n\n"
            "Наши социальные сети:\n"
            "🔹 [Telegram](https://t.me/rayyonpardalar)\n"
            "🔸 [Instagram](https://www.instagram.com/rayyon_pardalar)\n\n"
            "Нажмите кнопку ниже, чтобы начать расчет, или введите имя клиента:"
        )
        
        
    reply_markup = get_admin_kb() if message.from_user.id == ADMIN_ID else None
    await message.answer(msg, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True)
    await state.set_state(OrderProcess.waiting_name)

@dp.callback_query(F.data == "start_calc")
async def start_calc_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Mijoz ismini kiriting:")
    await state.set_state(OrderProcess.waiting_name)
    await callback.answer()

@dp.message(F.text == "📊 Mahsulotlar Hisoboti")
async def admin_report_btn(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    # Reuse the existing report logic or call the function
    await admin_report_msg(message)

@dp.message(F.text == "⚙️ Narxlar va Sozlamalar")
async def admin_settings_btn(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await show_settings_menu(message)

@dp.message(F.text == "👥 Foydalanuvchilar")
async def admin_users_btn(message: types.Message):
    await cmd_users(message)

async def admin_report_msg(message: types.Message):
    orders = load_orders()
    if not orders:
        await message.answer("Hali hech qanday buyurtma saqlanmagan.")
        return
    tyul_u, part_u = {}, {}
    for order in orders:
        for room in order.get('rooms', []):
            if room.get('tyul_on'):
                c = room.get('tyul_code', 'Noma\'lum')
                tyul_u[c] = tyul_u.get(c, 0) + float(room.get('tyul_metraj', 0))
            if room.get('part_on'):
                c = room.get('part_code', 'Noma\'lum')
                part_u[c] = part_u.get(c, 0) + float(room.get('part_metraj', 0))
    text = "📦 **Mahsulotlar Ishlatilishi Hisoboti**\n\n"
    if tyul_u:
        text += "▫️ **Tyullar:**\n"
        for c, m in tyul_u.items(): text += f"   • {c}: {m:.2f} metr\n"
        text += "\n"
    if part_u:
        text += "▫️ **Parterlar:**\n"
        for c, m in part_u.items(): text += f"   • {c}: {m:.2f} metr\n"
        text += "\n"
    if not tyul_u and not part_u: text += "Ma'lumot topilmadi."
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    users = load_users()
    if not users:
        await message.answer("Hali hech kim botga kirmagan.")
        return
    text = f"<b>👥 Jami foydalanuvchilar: {len(users)} ta</b>\n\n"
    users_list = list(users.values())
    for u in users_list[-20:]:
        safe_name = str(u['ism']).replace('<', '&lt;').replace('>', '&gt;')
        safe_uname = str(u['username']).replace('<', '&lt;').replace('>', '&gt;')
        text += f"• {safe_name} | {safe_uname} | <code>{u['sana']}</code> | ID: <code>{u['id']}</code>\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Ishlatish: /ban <USER_ID>")
        return
    try:
        user_id = int(args[1])
        ban_user(user_id)
        await message.answer(f"✅ Foydalanuvchi {user_id} bloklandi.")
    except: await message.answer("ID raqam bo'lishi kerak.")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Ishlatish: /unban <USER_ID>")
        return
    try:
        user_id = int(args[1])
        unban_user(user_id)
        await message.answer(f"✅ Foydalanuvchi {user_id} blokdan chiqarildi.")
    except: await message.answer("ID raqam bo'lishi kerak.")

# --- NAVIGATION HANDLERS ---
@dp.callback_query(F.data.startswith("back_to_"))
async def process_back_button(callback: types.CallbackQuery, state: FSMContext):
    target = callback.data.replace("back_to_", "")
    data = await state.get_data()
    
    if target == "name":
        await state.set_state(OrderProcess.waiting_name)
        await callback.message.answer("Mijoz ismini kiriting:")
    elif target == "room":
        await prompt_room_name(callback, state)
    elif target == "dims":
        await state.set_state(OrderProcess.waiting_dims)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_room")]])
        await callback.message.answer("O'lchamlarni kiriting (Eni va Bo'yi ketma-ketligida):\n(Masalan: 4.0 3.1)", reply_markup=kb)
    elif target == "skladka":
        await state.set_state(OrderProcess.waiting_skladka)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="1:2.0", callback_data="sk_2.0"), types.InlineKeyboardButton(text="1:2.5", callback_data="sk_2.5")],
                [types.InlineKeyboardButton(text="1:2.8", callback_data="sk_2.8"), types.InlineKeyboardButton(text="1:3.0", callback_data="sk_3.0")],
                [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_dims")]
            ]
        )
        await callback.message.answer("Skladkani tanlang:", reply_markup=kb)
    elif target == "components":
        await state.set_state(OrderProcess.waiting_components)
        await show_components_menu(callback.message, data)
    elif target == "tyul_narxi":
        await state.set_state(OrderProcess.waiting_tyul_narxi)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_components")]])
        await callback.message.answer("Tyulning kodi va 1 metr narxini kiriting:\n(Masalan: T-105 45000)", reply_markup=kb)
    elif target == "parter_narxi":
        await state.set_state(OrderProcess.waiting_parter_narxi)
        back_t = "back_to_tyul_narxi" if data.get('comp_tyul', True) else "back_to_components"
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_t)]])
        await callback.message.answer("Parterning kodi va 1 metr narxini kiriting:\n(Masalan: P-300 85000)", reply_markup=kb)
    elif target == "style":
        await go_to_style_direct(callback.message, state)
    
    await callback.answer()

@dp.callback_query(F.data == "admin_report")
async def admin_report(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    orders = load_orders()
    if not orders:
        await callback.message.answer("Hali hech qanday buyurtma saqlanmagan.")
        return
    tyul_u = {}
    part_u = {}
    for order in orders:
        for room in order.get('rooms', []):
            if room.get('tyul_on'):
                c = room.get('tyul_code', 'Noma\'lum')
                tyul_u[c] = tyul_u.get(c, 0) + float(room.get('tyul_metraj', 0))
            if room.get('part_on'):
                c = room.get('part_code', 'Noma\'lum')
                part_u[c] = part_u.get(c, 0) + float(room.get('part_metraj', 0))
    text = "📦 **Mahsulotlar Ishlatilishi Hisoboti**\n\n"
    if tyul_u:
        text += "▫️ **Tyullar:**\n"
        for c, m in tyul_u.items(): text += f"   • {c}: {m:.2f} metr\n"
        text += "\n"
    if part_u:
        text += "▫️ **Parterlar:**\n"
        for c, m in part_u.items(): text += f"   • {c}: {m:.2f} metr\n"
        text += "\n"
    if not tyul_u and not part_u: text += "Ma'lumot topilmadi."
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- 3. ISM, XONA VA O'LCHAM ---
@dp.message(StateFilter(OrderProcess.waiting_name))
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text, rooms=[])
    await prompt_room_name(message, state)

async def prompt_room_name(message_or_call, state: FSMContext):
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🛏 Yotoqxona (Spalni)", callback_data="room_Spalni"), types.InlineKeyboardButton(text="🛋 Mehmonxona (Zal)", callback_data="room_Zal")],
            [types.InlineKeyboardButton(text="🍽 Oshxona", callback_data="room_Oshxona"), types.InlineKeyboardButton(text="🧸 Bolalar xonasi", callback_data="room_Bolalar")],
            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_name")]
        ]
    )
    msg = "Xona nomini tugmalardan tanlang yoki o'zingiz yozib yuboring:"
    if isinstance(message_or_call, types.Message): await message_or_call.answer(msg, reply_markup=kb)
    else: await message_or_call.message.answer(msg, reply_markup=kb)
    await state.set_state(OrderProcess.waiting_room_name)

@dp.callback_query(StateFilter(OrderProcess.waiting_room_name), F.data.startswith('room_'))
async def process_room_cb(callback: types.CallbackQuery, state: FSMContext):
    room_base = callback.data.split('_')[1]
    mapping = {"Zal": "Mehmonxona (Zal)", "Spalni": "Yotoqxona (Spalni)", "Oshxona": "Oshxona", "Bolalar": "Bolalar xonasi"}
    await set_room_name(mapping.get(room_base, room_base), callback.message, state)

@dp.message(StateFilter(OrderProcess.waiting_room_name))
async def get_room_name(message: types.Message, state: FSMContext):
    await set_room_name(message.text, message, state)

async def set_room_name(room_base_name: str, message: types.Message, state: FSMContext):
    data = await state.get_data()
    rooms = data.get('rooms', [])
    count = sum(1 for r in rooms if r.get('room_base') == room_base_name)
    final_name = room_base_name if count == 0 else f"{room_base_name} {count + 1}"
    await state.update_data(room_name=final_name, room_base=room_base_name)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_room")]])
    await message.answer(f"✅ Tanlandi: {final_name}\n\nEndi o'lchamlarni kiriting (Eni va Bo'yi ketma-ketligida):\n(Masalan: 4.0 3.1)", reply_markup=kb)
    await state.set_state(OrderProcess.waiting_dims)

@dp.message(StateFilter(OrderProcess.waiting_dims))
async def get_dims(message: types.Message, state: FSMContext):
    try:
        w, h = map(float, message.text.split())
        await state.update_data(width=w, height=h)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="1:2.0", callback_data="sk_2.0"), types.InlineKeyboardButton(text="1:2.5", callback_data="sk_2.5")],
                [types.InlineKeyboardButton(text="1:2.8", callback_data="sk_2.8"), types.InlineKeyboardButton(text="1:3.0", callback_data="sk_3.0")],
                [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_dims")]
            ]
        )
        await message.answer("Skladkani tanlang:", reply_markup=kb)
        await state.set_state(OrderProcess.waiting_skladka)
    except: await message.answer("❌ Xato! O'lchamni '3.5 2.8' ko'rinishida yozing.")

@dp.callback_query(StateFilter(OrderProcess.waiting_skladka), F.data.startswith('sk_'))
async def get_skladka(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(skladka=float(callback.data.split('_')[1]))
    await state.update_data(comp_tyul=True, comp_zash=True, comp_part=False)
    await show_components_menu(callback.message, await state.get_data())
    await state.set_state(OrderProcess.waiting_components)

async def show_components_menu(message: types.Message, data: dict):
    t_on, z_on, p_on = data.get('comp_tyul', True), data.get('comp_zash', True), data.get('comp_part', False)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Tyul" if t_on else "❌ Tyul", callback_data="comp_tyul"),
             types.InlineKeyboardButton(text="✅ Zashitka" if z_on else "❌ Zashitka", callback_data="comp_zash"),
             types.InlineKeyboardButton(text="✅ Parter" if p_on else "❌ Parter", callback_data="comp_part")],
            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_skladka")],
            [types.InlineKeyboardButton(text="➡️ DAVOM ETISH", callback_data="next_step")]
        ]
    )
    await message.edit_text("Parda tarkibini tanlang:", reply_markup=kb)

@dp.callback_query(StateFilter(OrderProcess.waiting_components), F.data.startswith('comp_'))
async def toggle_component(callback: types.CallbackQuery, state: FSMContext):
    c_type = callback.data
    data = await state.get_data()
    val = data.get(c_type, True if c_type in ['comp_tyul', 'comp_zash'] else False)
    await state.update_data({c_type: not val})
    await show_components_menu(callback.message, await state.get_data())

@dp.callback_query(StateFilter(OrderProcess.waiting_components), F.data == "next_step")
async def prompt_tyul_yoki_parter(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('comp_tyul', True):
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_components")]])
        await callback.message.edit_text("Tyulning kodi va 1 metr narxini kiriting:\n(Masalan: T-105 45000)", reply_markup=kb)
        await state.set_state(OrderProcess.waiting_tyul_narxi)
    else: await check_and_prompt_parter(callback.message, state)

@dp.message(StateFilter(OrderProcess.waiting_tyul_narxi))
async def get_tyul_narxi(message: types.Message, state: FSMContext):
    text = message.text.split()
    if len(text) >= 2:
        try:
            p = float(text[-1].replace('.', '').replace(',', ''))
            await state.update_data(tyul_code=" ".join(text[:-1]), tyul_price=p)
            await check_and_prompt_parter(message, state)
        except: await message.answer("Masalan: T-105 45000")
    else: await message.answer("Iltimos to'liq kiriting: kod va narx.")

async def check_and_prompt_parter(m_or_c, state: FSMContext):
    data = await state.get_data()
    if data.get('comp_part', False):
        back_t = "back_to_tyul_narxi" if data.get('comp_tyul', True) else "back_to_components"
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_t)]])
        msg = "Parterning kodi va 1 metr narxini kiriting:\n(Masalan: P-300 85000)"
        if isinstance(m_or_c, types.Message): await m_or_c.answer(msg, reply_markup=kb)
        else: await m_or_c.edit_text(msg, reply_markup=kb)
        await state.set_state(OrderProcess.waiting_parter_narxi)
    else: await go_to_style_direct(m_or_c, state)

@dp.message(StateFilter(OrderProcess.waiting_parter_narxi))
async def get_parter_narxi(message: types.Message, state: FSMContext):
    text = message.text.split()
    if len(text) >= 2:
        try:
            p = float(text[-1].replace('.', '').replace(',', ''))
            await state.update_data(part_code=" ".join(text[:-1]), part_price=p)
            await go_to_style_direct(message, state)
        except: await message.answer("Masalan: P-300 85000")
    else: await message.answer("Iltimos to'liq kiriting: kod va narx.")

async def go_to_style_direct(m_or_c, state: FSMContext):
    data = await state.get_data()
    back_t = "back_to_parter_narxi" if data.get('comp_part', False) else ("back_to_tyul_narxi" if data.get('comp_tyul', True) else "back_to_components")
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎀 Karsaj", callback_data="style_karsaj"), types.InlineKeyboardButton(text="✨ Karset", callback_data="style_karset")],
        [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_t)]
    ])
    msg = "Pardaning yuqori qismiga nima tikamiz?"
    if isinstance(m_or_c, types.Message): await m_or_c.answer(msg, reply_markup=kb)
    else: await m_or_c.edit_text(msg, reply_markup=kb)
    await state.set_state(OrderProcess.waiting_style)

@dp.callback_query(StateFilter(OrderProcess.waiting_style), F.data.startswith('style_'))
async def process_style(callback: types.CallbackQuery, state: FSMContext):
    s_type = callback.data.split('_')[1]
    await state.update_data(style=s_type)
    if s_type == 'karsaj': await execute_calculate_final(callback.message, state)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🟡 Radnoy kalso", callback_data="kalso_radnoy"), types.InlineKeyboardButton(text="⚪ Oddiy kalso", callback_data="kalso_oddiy")],
            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_style")]
        ])
        await callback.message.edit_text("Halqa (Kalso) turini tanlang:", reply_markup=kb)
        await state.set_state(OrderProcess.waiting_kalso)

@dp.callback_query(StateFilter(OrderProcess.waiting_kalso), F.data.startswith('kalso_'))
async def process_kalso(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(kalso=callback.data.split('_')[1])
    await execute_calculate_final(callback.message, state)

async def execute_calculate_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    w, h, sk = data['width'], data['height'], data['skladka']
    t_on, z_on, p_on = data.get('comp_tyul', True), data.get('comp_zash', True), data.get('comp_part', False)
    t_price, p_price = data.get('tyul_price', 0), data.get('part_price', 0)
    s_type, k_type = data.get('style', 'karsaj'), data.get('kalso', None)
    
    mato_m, part_m, tik_s, tik_m, zash_s, t_m_s, p_m_s, kars_m = 0, 0, 0, 0, 0, 0, 0, 0
    if t_on:
        mato_m = (w * sk) + 0.20
        tik_m += mato_m
        tik_s += mato_m * float(PRICES['tikuv'])
        t_m_s = mato_m * t_price
        kars_m += w
    if p_on:
        part_m = (h + 0.20) * 2
        tik_m += part_m
        tik_s += part_m * float(PRICES['tikuv'])
        p_m_s = part_m * p_price
        kars_m += 1.8
    if z_on:
        zm = w + 0.20
        zash_s = zm * float(PRICES['zashitka'])
        tik_m += zm
        tik_s += zm * float(PRICES['tikuv'])
        kars_m += w
            
    t_nomi, t_s, t_m_show, t_n, k_s, k_soni, k_n = "", 0, 0, 0, 0, 0, 0
    if s_type == 'karsaj':
        t_nomi, t_n = "Karsaj", float(PRICES['karsaj'])
        t_s, t_m_show = kars_m * t_n, kars_m
    else:
        t_nomi, t_n = "Karset", float(PRICES['karset'])
        if k_type == 'oddiy':
            t_m_show = kars_m
            t_s, k_soni, k_n = t_m_show * t_n, int(t_m_show * 10), float(PRICES['oddiy_kalso'])
            k_s = k_soni * k_n
        elif k_type == 'radnoy':
            t_m_show = part_m
            t_s, k_soni, k_n = t_m_show * t_n, int(t_m_show / 0.15), float(PRICES['radnoy_kalso'])
            k_s = k_soni * k_n
            
    jami = float(tik_s) + float(zash_s) + float(t_s) + float(k_s) + float(t_m_s) + float(p_m_s)
    def f_n(n): return f"{n:,.0f}"
    r_name = data.get('room_name', '')
    text = f"🏠 Xona: {r_name}\n\n"
    if t_on: text += f"Tyul ({data.get('tyul_code')}): {mato_m:.2f} m × {f_n(t_price)} = {f_n(t_m_s)}\n\n"
    if p_on: text += f"Parter ({data.get('part_code')}): {part_m:.2f} m × {f_n(p_price)} = {f_n(p_m_s)}\n\n"
    if z_on: text += f"Zashitka: {w+0.20:.2f} m × {f_n(PRICES['zashitka'])} = {f_n(zash_s)}\n\n"
    if t_m_show > 0:
        text += f"{t_nomi}: {t_m_show:.2f} m × {f_n(t_n)} = {f_n(t_s)}\n\n"
        if k_soni > 0: text += f"Kalso ({k_type}): {k_soni} ta × {f_n(k_n)} = {f_n(k_s)}\n\n"
    if tik_m > 0: text += f"Tikuv xizmati: {tik_m:.2f} m × {f_n(PRICES['tikuv'])} = {f_n(tik_s)}\n\n"
    text += f"Xona jami: {f_n(jami)} so'm"
    
    room_obj = {'room_name': r_name, 'room_base': data.get('room_base'), 'width': w, 'height': h, 'skladka': sk,
                'tyul_on': t_on, 'tyul_code': data.get('tyul_code'), 'tyul_price': t_price, 'tyul_metraj': mato_m, 
                'part_on': p_on, 'part_code': data.get('part_code'), 'part_price': p_price, 'part_metraj': part_m,
                'zash_on': z_on, 'zash_summa': zash_s, 'jami': jami, 'text': text}
    rooms = data.get('rooms', [])
    rooms.append(room_obj)
    await state.update_data(rooms=rooms)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Yana xona qo'shish", callback_data="add_room")],
        [types.InlineKeyboardButton(text="📄 Yakunlash (Hisobot olish)", callback_data="finish_order")]
    ])
    if isinstance(message, types.Message): await message.answer(text, reply_markup=kb)
    else: await message.edit_text(text, reply_markup=kb)
    await state.set_state(OrderProcess.waiting_next_action)

@dp.callback_query(StateFilter(OrderProcess.waiting_next_action), F.data == "add_room")
async def go_to_add_room(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comp_tyul=True, comp_zash=True, comp_part=False, tyul_code='', tyul_price=0, part_code='', part_price=0, style='karsaj', kalso=None, width=None, height=None, skladka=None)
    await prompt_room_name(callback, state)

@dp.callback_query(StateFilter(OrderProcess.waiting_next_action), F.data == "finish_order")
async def finish_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rooms, client_name = data.get('rooms', []), data.get('name', 'Mijoz')
    def f_n(n): return f"{n:,.0f}"
    final_text = f"👤 Mijoz: {client_name}\n=====================\n\n"
    total_summa = 0
    for r in rooms:
        final_text += f"{r['text']}\n\n---------------------\n\n"
        total_summa += r['jami']
    final_text += f"\n💰 **UMUMIY HISOB: {f_n(total_summa)} so'm**\n"
    final_text += "---------------------\n✂️ Bizni tanlaganingiz uchun rahmat!\n"
    final_text += "📱 [Telegram](https://t.me/rayyonpardalar) | 📸 [Instagram](https://www.instagram.com/rayyon_pardalar)"
    # 3 ta chek muammosini hal qilish uchun keyboardni o'chiramiz
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Buyurtma ma'lumotlarini to'plash
    order_data = {
        'client_name': client_name,
        'user_id': callback.from_user.id,
        'username': callback.from_user.username,
        'rooms': rooms,
        'total_summa': total_summa,
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    try:
        # Rasm chekni tayyorlash
        photo_path = generate_receipt_image(order_data)
        photo = FSInputFile(photo_path)
        
        # Faqat bitta rasm yuboramiz (matnli chek o'rniga)
        await bot.send_photo(callback.from_user.id, photo, caption="✅ Buyurtmangiz hisob-kitob qilindi!")
        
        # Adminga ham yuborish
        await bot.send_photo(ADMIN_ID, photo, caption=f"🗄 **YANGI BUYURTMA (Mijoz: {client_name})**")
        
        # Hisob-kitob yakunlandi va chek yuborildi.
        await callback.message.edit_text("📄 Hisob-kitob yakunlandi va chek yuborildi.")
            
    except Exception as e:
        print(f"Rasm yaratishda xatolik: {e}")
        # Agar rasmda xato bo'lsa, eski matnli usulga qaytamiz
        await callback.message.edit_text(final_text, parse_mode="Markdown", disable_web_page_preview=True)
        await bot.send_message(ADMIN_ID, f"🗄 **YANGI BUYURTMA (MATNLI):**\n\n{final_text}", parse_mode="Markdown")

    save_order(order_data)
    await state.clear()

@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await show_settings_menu(message)

async def show_settings_menu(m_or_c):
    lang = PRICES.get('lang', 'uz')
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🌐 Til: {'🇺🇿 O‘zbek' if lang == 'uz' else '🇷🇺 Русский'}", callback_data="set_lang_toggle")],
        [types.InlineKeyboardButton(text=f"🛡 Zashitka: {PRICES['zashitka']:,.0f}", callback_data="set_zashitka")],
        [types.InlineKeyboardButton(text=f"🧵 Tikuv: {PRICES['tikuv']:,.0f}", callback_data="set_tikuv")],
        [types.InlineKeyboardButton(text=f"🎀 Karsaj: {PRICES['karsaj']:,.0f}", callback_data="set_karsaj")],
        [types.InlineKeyboardButton(text=f"✨ Karset: {PRICES['karset']:,.0f}", callback_data="set_karset")],
        [types.InlineKeyboardButton(text=f"🟡 Radnoy kalso: {PRICES['radnoy_kalso']:,.0f}", callback_data="set_radnoy_kalso")],
        [types.InlineKeyboardButton(text=f"⚪ Oddiy kalso: {PRICES['oddiy_kalso']:,.0f}", callback_data="set_oddiy_kalso")],
        [types.InlineKeyboardButton(text="📦 Mahsulotlar Hisoboti", callback_data="admin_report")],
        [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="set_cancel")]
    ])
    msg = "⚙️ **Sozlamalar (Narxlar va Til)**\n\nO'zgartirmoqchi bo'lgan ma'lumotni tanlang:"
    if isinstance(m_or_c, types.Message): await m_or_c.answer(msg, reply_markup=kb, parse_mode="Markdown")
    else: await m_or_c.edit_text(msg, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith('set_'))
async def process_settings_cb(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    action = callback.data.replace('set_', '')
    if action == 'cancel':
        await callback.message.edit_text("⚙️ Sozlamalar yopildi.")
        return
    if action == 'lang_toggle':
        PRICES['lang'] = 'ru' if PRICES.get('lang', 'uz') == 'uz' else 'uz'
        save_prices(PRICES)
        await show_settings_menu(callback.message)
        return
    await state.update_data(setting_key=action)
    await callback.message.edit_text(f"Yangi narxni yozing (masalan, 5000):")
    await state.set_state(SettingsProcess.waiting_for_price)

@dp.message(StateFilter(SettingsProcess.waiting_for_price))
async def update_price_value(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    try:
        p = float(message.text.replace('.', '').replace(',', '').replace(' ', ''))
        PRICES[data.get('setting_key')] = p
        save_prices(PRICES)
        await message.answer(f"✅ Narx muvaffaqiyatli saqlandi!")
        await show_settings_menu(message)
        await state.set_state(None)
    except: await message.answer("Iltimos, faqat raqam kiriting!")

async def main(): await dp.start_polling(bot)
if __name__ == '__main__': asyncio.run(main())
