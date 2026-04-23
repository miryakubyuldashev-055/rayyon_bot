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

# --- SOZLAMALAR ---
API_TOKEN = os.getenv('BOT_TOKEN', '8797944374:AAE7xuw_RR5bhLIrFOxAYxXhy9HGB_cMBc8')
ADMIN_ID = 5094694146

PRICES_FILE = 'prices.json'
USERS_FILE = 'users.json'
BANNED_FILE = 'banned.json'

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
    "zashitka": 22000,
    "tikuv": 40000,
    "karsaj": 5000,
    "karset": 12000,
    "radnoy_kalso": 7000,
    "oddiy_kalso": 3000,
    "lang": "uz"
}

def load_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_PRICES.copy()

def save_prices(prices):
    with open(PRICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=4)

PRICES = load_prices()

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
    
    # Bloklangan foydalanuvchini tekshirish
    if is_banned(message.from_user.id):
        await message.answer("⛔ Siz bu botdan foydalanish imkoniyatingizdan mahrum qilindingiz.")
        return
    
    # Foydalanuvchini saqlash
    user = message.from_user
    save_user(user)
    
    # Adminga bildirishnoma
    if user.id != ADMIN_ID:
        uname = f'@{user.username}' if user.username else 'Yo\'q'
        notif = f"👤 Yangi foydalanuvchi botga kirdi!\n\n🪪 Ism: {user.full_name}\n🔗 Username: {uname}\n🆔 ID: {user.id}"
        try:
            await bot.send_message(ADMIN_ID, notif)
        except Exception:
            pass
    
    lang = PRICES.get('lang', 'uz')
    if lang == 'uz':
        msg = "👋 **Rayyon Pardalar** hisob-kitob tizimiga xush kelibsiz!\n\nMijoz ismini kiriting:"
    else:
        msg = "👋 Добро пожаловать в систему расчета **Rayyon Pardalar**!\n\nВведите имя клиента:"
        
    await message.answer(msg, parse_mode="Markdown")
    await state.set_state(OrderProcess.waiting_name)


@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    if not users:
        await message.answer("Hali hech kim botga kirmagan.")
        return
    
    text = f"<b>👥 Jami foydalanuvchilar: {len(users)} ta</b>\n\n"
    
    # Oxirgi 20 ta foydalanuvchi
    users_list = list(users.values())
    for u in users_list[-20:]:
        # HTML uchun maxsus belgilarni tozalash
        safe_name = str(u['ism']).replace('<', '&lt;').replace('>', '&gt;')
        safe_uname = str(u['username']).replace('<', '&lt;').replace('>', '&gt;')
        
        text += f"• {safe_name} | {safe_uname} | <code>{u['sana']}</code> | ID: <code>{u['id']}</code>\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Ishtatish: /ban <USER_ID>")
        return
    try:
        user_id = int(args[1])
        ban_user(user_id)
        await message.answer(f"✅ Foydalanuvchi {user_id} bloklandi.")
    except ValueError:
        await message.answer("ID raqam bo'lishi kerak.")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Ishlatish: /unban <USER_ID>")
        return
    try:
        user_id = int(args[1])
        unban_user(user_id)
        await message.answer(f"✅ Foydalanuvchi {user_id} blokdan chiqarildi.")
    except ValueError:
        await message.answer("ID raqam bo'lishi kerak.")

# --- 3. ISM, XONA VA O'LCHAM ---
@dp.message(StateFilter(OrderProcess.waiting_name))
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text, rooms=[])
    await prompt_room_name(message, state)

async def prompt_room_name(message_or_call, state: FSMContext):
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🛏 Yotoqxona (Spalni)", callback_data="room_Spalni"),
                types.InlineKeyboardButton(text="🛋 Mehmonxona (Zal)", callback_data="room_Zal")
            ],
            [
                types.InlineKeyboardButton(text="🍽 Oshxona", callback_data="room_Oshxona"),
                types.InlineKeyboardButton(text="🧸 Bolalar xonasi", callback_data="room_Bolalar")
            ]
        ]
    )
    
    msg = "Xona nomini tugmalardan tanlang yoki o'zingiz yozib yuboring:"
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(msg, reply_markup=kb)
    else:
        await message_or_call.message.answer(msg, reply_markup=kb)
    await state.set_state(OrderProcess.waiting_room_name)

@dp.callback_query(StateFilter(OrderProcess.waiting_room_name), F.data.startswith('room_'))
async def process_room_cb(callback: types.CallbackQuery, state: FSMContext):
    room_base = callback.data.split('_')[1]
    mapping = {
        "Zal": "Mehmonxona (Zal)",
        "Spalni": "Yotoqxona (Spalni)",
        "Oshxona": "Oshxona",
        "Bolalar": "Bolalar xonasi"
    }
    room_base_name = mapping.get(room_base, room_base)
    await set_room_name(room_base_name, callback.message, state)

@dp.message(StateFilter(OrderProcess.waiting_room_name))
async def get_room_name(message: types.Message, state: FSMContext):
    await set_room_name(message.text, message, state)

async def set_room_name(room_base_name: str, message: types.Message, state: FSMContext):
    data = await state.get_data()
    rooms = data.get('rooms', [])
    
    count = sum(1 for r in rooms if r.get('room_base') == room_base_name)
    if count == 0:
        final_room_name = room_base_name
    else:
        final_room_name = f"{room_base_name} {count + 1}"
        
    await state.update_data(room_name=final_room_name, room_base=room_base_name)
    
    msg = f"✅ Tanlandi: {final_room_name}\n\nEndi o'lchamlarni kiriting (Eni va Bo'yi ketma-ketligida):\n(Masalan: 4.0 3.1)"
    await message.answer(msg)
    await state.set_state(OrderProcess.waiting_dims)

@dp.message(StateFilter(OrderProcess.waiting_dims))
async def get_dims(message: types.Message, state: FSMContext):
    try:
        w, h = map(float, message.text.split())
        await state.update_data(width=w, height=h)
        
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="1:2.0", callback_data="sk_2.0"),
                    types.InlineKeyboardButton(text="1:2.5", callback_data="sk_2.5")
                ],
                [
                    types.InlineKeyboardButton(text="1:2.8", callback_data="sk_2.8"),
                    types.InlineKeyboardButton(text="1:3.0", callback_data="sk_3.0")
                ]
            ]
        )
        await message.answer("Skladkani tanlang:", reply_markup=kb)
        await state.set_state(OrderProcess.waiting_skladka)
    except ValueError:
        await message.answer("❌ Xato! O'lchamni '3.5 2.8' ko'rinishida yozing.")

@dp.callback_query(StateFilter(OrderProcess.waiting_skladka), F.data.startswith('sk_'))
async def get_skladka(callback: types.CallbackQuery, state: FSMContext):
    sklad = float(callback.data.split('_')[1])
    await state.update_data(skladka=sklad)
    
    await state.update_data(comp_tyul=True, comp_zash=True, comp_part=False)
    await show_components_menu(callback.message, await state.get_data())
    await state.set_state(OrderProcess.waiting_components)

async def show_components_menu(message: types.Message, data: dict):
    tyul_on = data.get('comp_tyul', True)
    zash_on = data.get('comp_zash', True)
    part_on = data.get('comp_part', False)
    
    t_text = "✅ Tyul" if tyul_on else "❌ Tyul"
    z_text = "✅ Zashitka" if zash_on else "❌ Zashitka"
    p_text = "✅ Parter" if part_on else "❌ Parter"
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=t_text, callback_data="comp_tyul"),
                types.InlineKeyboardButton(text=z_text, callback_data="comp_zash"),
                types.InlineKeyboardButton(text=p_text, callback_data="comp_part")
            ],
            [types.InlineKeyboardButton(text="➡️ DAVOM ETISH", callback_data="next_step")]
        ]
    )
    
    msg = "Parda tarkibini tanlang (yoqish/o'chirish uchun ustiga bosing):"
    await message.edit_text(msg, reply_markup=kb)

@dp.callback_query(StateFilter(OrderProcess.waiting_components), F.data.startswith('comp_'))
async def toggle_component(callback: types.CallbackQuery, state: FSMContext):
    comp_type = callback.data # comp_tyul, comp_zash, comp_part
    data = await state.get_data()
    
    current_val = data.get(comp_type, False)
    if comp_type == 'comp_tyul' and 'comp_tyul' not in data:
        current_val = True
    if comp_type == 'comp_zash' and 'comp_zash' not in data:
        current_val = True
        
    await state.update_data({comp_type: not current_val})
    new_data = await state.get_data()
    
    await show_components_menu(callback.message, new_data)

@dp.callback_query(StateFilter(OrderProcess.waiting_components), F.data == "next_step")
async def prompt_tyul_yoki_parter(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('comp_tyul', True):
        msg = "Tyulning kodi va 1 metr narxini kiriting:\n(Masalan: T-105 45000)"
        await callback.message.edit_text(msg)
        await state.set_state(OrderProcess.waiting_tyul_narxi)
    else:
        await check_and_prompt_parter(callback.message, state)

@dp.message(StateFilter(OrderProcess.waiting_tyul_narxi))
async def get_tyul_narxi(message: types.Message, state: FSMContext):
    text = message.text.split()
    if len(text) >= 2:
        tyul_code = " ".join(text[:-1])
        try:
            price_str = text[-1].replace('.', '').replace(',', '')
            await state.update_data(tyul_code=tyul_code, tyul_price=float(price_str))
            await check_and_prompt_parter(message, state)
        except ValueError:
            await message.answer("Masalan: T-105 45000")
    else:
        await message.answer("Iltimos to'liq kiriting: kod va narx.")

async def check_and_prompt_parter(message_or_call, state: FSMContext):
    data = await state.get_data()
    if data.get('comp_part', False):
        msg = "Parterning kodi va 1 metr narxini kiriting:\n(Masalan: P-300 85000)"
        if isinstance(message_or_call, types.Message):
            await message_or_call.answer(msg)
        else:
            await message_or_call.edit_text(msg)
        await state.set_state(OrderProcess.waiting_parter_narxi)
    else:
        await go_to_style_direct(message_or_call, state)

@dp.message(StateFilter(OrderProcess.waiting_parter_narxi))
async def get_parter_narxi(message: types.Message, state: FSMContext):
    text = message.text.split()
    if len(text) >= 2:
        part_code = " ".join(text[:-1])
        try:
            price_str = text[-1].replace('.', '').replace(',', '')
            await state.update_data(part_code=part_code, part_price=float(price_str))
            await go_to_style_direct(message, state)
        except ValueError:
            await message.answer("Masalan: P-300 85000")
    else:
        await message.answer("Iltimos to'liq kiriting: kod va narx.")

async def go_to_style_direct(message_or_call, state: FSMContext):
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="🎀 Karsaj", callback_data="style_karsaj"),
            types.InlineKeyboardButton(text="✨ Karset", callback_data="style_karset")
        ]]
    )
    
    msg = "Pardaning yuqori qismiga nima tikamiz?"
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(msg, reply_markup=kb)
    else:
        await message_or_call.edit_text(msg, reply_markup=kb)
    await state.set_state(OrderProcess.waiting_style)

@dp.callback_query(StateFilter(OrderProcess.waiting_style), F.data.startswith('style_'))
async def process_style(callback: types.CallbackQuery, state: FSMContext):
    style_type = callback.data.split('_')[1]
    await state.update_data(style=style_type)
    
    if style_type == 'karsaj':
        await execute_calculate_final(callback.message, state)
    else:
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(text="🟡 Radnoy kalso", callback_data="kalso_radnoy"),
                types.InlineKeyboardButton(text="⚪ Oddiy kalso", callback_data="kalso_oddiy")
            ]]
        )
        await callback.message.edit_text("Halqa (Kalso) turini tanlang:", reply_markup=kb)
        await state.set_state(OrderProcess.waiting_kalso)

@dp.callback_query(StateFilter(OrderProcess.waiting_kalso), F.data.startswith('kalso_'))
async def process_kalso(callback: types.CallbackQuery, state: FSMContext):
    kalso_type = callback.data.split('_')[1]
    await state.update_data(kalso=kalso_type)
    await execute_calculate_final(callback.message, state)

async def execute_calculate_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    w = data['width']
    h = data['height']
    sk = data['skladka']
    
    tyul_on = data.get('comp_tyul', True)
    zash_on = data.get('comp_zash', True)
    part_on = data.get('comp_part', False)
    
    tyul_code = data.get('tyul_code', '')
    tyul_price = data.get('tyul_price', 0)
    part_code = data.get('part_code', '')
    part_price = data.get('part_price', 0)
    
    style_type = data.get('style', 'karsaj')
    kalso_type = data.get('kalso', None)
    
    mato_metraj = 0
    parter_metraj = 0
    tikuv_summa = 0
    tikuv_metraj = 0
    zash_summa = 0
    tyul_mato_summa = 0
    parter_mato_summa = 0
    asosiy_karsaj_metrati = 0
    
    if tyul_on:
        mato_metraj = (w * sk) + 0.20
        tikuv_metraj += mato_metraj
        tikuv_summa += mato_metraj * PRICES['tikuv']
        tyul_mato_summa = mato_metraj * tyul_price
        asosiy_karsaj_metrati += w
            
    if part_on:
        parter_metraj = (h + 0.20) * 2
        tikuv_metraj += parter_metraj
        tikuv_summa += parter_metraj * PRICES['tikuv']
        parter_mato_summa = parter_metraj * part_price
        asosiy_karsaj_metrati += 1.8
            
    if zash_on:
        zash_summa = (w + 0.20) * PRICES['zashitka']
        asosiy_karsaj_metrati += w
            
    tasma_nomi = ""
    tasma_summa = 0
    tasma_metrati_to_show = 0
    tasma_narxi = 0
    kalso_summa = 0
    kalso_soni = 0
    kalso_narxi = 0
    
    if style_type == 'karsaj':
        tasma_nomi = "Karsaj"
        tasma_narxi = PRICES['karsaj']
        tasma_summa = asosiy_karsaj_metrati * tasma_narxi
        tasma_metrati_to_show = asosiy_karsaj_metrati
    else:
        if kalso_type == 'oddiy':
            tasma_nomi = "Karset"
            tasma_metrati_to_show = asosiy_karsaj_metrati
            tasma_narxi = PRICES['karset']
            tasma_summa = tasma_metrati_to_show * tasma_narxi
            kalso_soni = int(tasma_metrati_to_show * 10)
            kalso_narxi = PRICES['oddiy_kalso']
            kalso_summa = kalso_soni * kalso_narxi
        elif kalso_type == 'radnoy':
            tasma_nomi = "Karset"
            tasma_metrati_to_show = parter_metraj 
            tasma_narxi = PRICES['karset']
            tasma_summa = tasma_metrati_to_show * tasma_narxi
            kalso_soni = int(tasma_metrati_to_show / 0.15)
            kalso_narxi = PRICES['radnoy_kalso']
            kalso_summa = kalso_soni * kalso_narxi
            
    jami = tikuv_summa + zash_summa + tasma_summa + kalso_summa + tyul_mato_summa + parter_mato_summa
    
    def format_num(n):
        return f"{n:,.0f}".replace(',', ',')
        
    room_name = data.get('room_name', '')
    text = f"🏠 Xona: {room_name}\n\n"
    
    if tyul_on:
        text += f"Tyul ({tyul_code}): {mato_metraj:.2f} m × {format_num(tyul_price)} = {format_num(tyul_mato_summa)}\n\n"
    if part_on:
        text += f"Parter ({part_code}): {parter_metraj:.2f} m × {format_num(part_price)} = {format_num(parter_mato_summa)}\n\n"
    if zash_on:
        text += f"Zashitka: {w+0.20:.2f} m × {format_num(PRICES['zashitka'])} = {format_num(zash_summa)}\n\n"
    if tasma_metrati_to_show > 0:
        text += f"{tasma_nomi}: {tasma_metrati_to_show:.2f} m × {format_num(tasma_narxi)} = {format_num(tasma_summa)}\n\n"
        if kalso_soni > 0:
            text += f"Kalso ({kalso_type}): {kalso_soni} ta × {format_num(kalso_narxi)} = {format_num(kalso_summa)}\n\n"
    if tikuv_metraj > 0:
        text += f"Tikuv xizmati: {tikuv_metraj:.2f} m × {format_num(PRICES['tikuv'])} = {format_num(tikuv_summa)}\n\n"
        
    text += f"Xona jami: {format_num(jami)} so'm"
    
    room_obj = {
        'room_name': room_name,
        'room_base': data.get('room_base', ''),
        'jami': jami,
        'text': text
    }
    rooms = data.get('rooms', [])
    rooms.append(room_obj)
    await state.update_data(rooms=rooms)
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Yana xona qo'shish", callback_data="add_room")],
            [types.InlineKeyboardButton(text="📄 Yakunlash (Hisobot olish)", callback_data="finish_order")]
        ]
    )
    
    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=kb)
    else:
        await message.edit_text(text, reply_markup=kb)
        
    await state.set_state(OrderProcess.waiting_next_action)

@dp.callback_query(StateFilter(OrderProcess.waiting_next_action), F.data == "add_room")
async def go_to_add_room(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        comp_tyul=True, comp_zash=True, comp_part=False,
        tyul_code='', tyul_price=0, part_code='', part_price=0,
        style='karsaj', kalso=None,
        width=None, height=None, skladka=None
    )
    await prompt_room_name(callback, state)

@dp.callback_query(StateFilter(OrderProcess.waiting_next_action), F.data == "finish_order")
async def finish_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rooms = data.get('rooms', [])
    client_name = data.get('name', 'Mijoz')
    
    def format_num(n):
        return f"{n:,.0f}".replace(',', ',')
        
    final_text = f"👤 Mijoz: {client_name}\n"
    final_text += "=====================\n\n"
    
    total_summa = 0
    for r in rooms:
        final_text += f"{r['text']}\n\n---------------------\n\n"
        total_summa += r['jami']
        
    final_text += f"💰 **UMUMIY HISOB: {format_num(total_summa)} so'm**\n"
    
    await callback.message.edit_text(final_text)
    await callback.message.answer("Buyurtmangiz qabul qilindi!")
    
    try:
        await bot.send_message(ADMIN_ID, f"🗄 **YANGI BUYURTMA (ARXIV):**\n\n{final_text}")
    except Exception as e:
        print(f"Adminga yuborishda xatolik: {e}")
        
    await state.clear()


# --- 8. ADMIN SOZLAMALAR ---
@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await show_settings_menu(message)

async def show_settings_menu(message_or_call):
    lang = PRICES.get('lang', 'uz')
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"🌐 Til: {'🇺🇿 O\'zbek' if lang == 'uz' else '🇷🇺 Русский'}", callback_data="set_lang_toggle")],
            [types.InlineKeyboardButton(text=f"🛡 Zashitka: {PRICES['zashitka']:,.0f}", callback_data="set_zashitka")],
            [types.InlineKeyboardButton(text=f"🧵 Tikuv: {PRICES['tikuv']:,.0f}", callback_data="set_tikuv")],
            [types.InlineKeyboardButton(text=f"🎀 Karsaj: {PRICES['karsaj']:,.0f}", callback_data="set_karsaj")],
            [types.InlineKeyboardButton(text=f"✨ Karset: {PRICES['karset']:,.0f}", callback_data="set_karset")],
            [types.InlineKeyboardButton(text=f"🟡 Radnoy kalso: {PRICES['radnoy_kalso']:,.0f}", callback_data="set_radnoy_kalso")],
            [types.InlineKeyboardButton(text=f"⚪ Oddiy kalso: {PRICES['oddiy_kalso']:,.0f}", callback_data="set_oddiy_kalso")],
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="set_cancel")]
        ]
    )
    
    msg = "⚙️ **Sozlamalar (Narxlar va Til)**\n\nO'zgartirmoqchi bo'lgan ma'lumotni tanlang:"
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(msg, reply_markup=kb, parse_mode="Markdown")
    else:
        await message_or_call.edit_text(msg, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith('set_'))
async def process_settings_cb(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    
    action = callback.data.replace('set_', '')
    if action == 'cancel':
        await callback.message.edit_text("⚙️ Sozlamalar yopildi.")
        return
        
    if action == 'lang_toggle':
        current_lang = PRICES.get('lang', 'uz')
        PRICES['lang'] = 'ru' if current_lang == 'uz' else 'uz'
        save_prices(PRICES)
        await show_settings_menu(callback.message)
        return
        
    await state.update_data(setting_key=action)
    await callback.message.edit_text(f"Yangi narxni yozing (masalan, 5000):")
    await state.set_state(SettingsProcess.waiting_for_price)

@dp.message(StateFilter(SettingsProcess.waiting_for_price))
async def update_price_value(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    data = await state.get_data()
    key = data.get('setting_key')
    
    try:
        price_str = message.text.replace('.', '').replace(',', '').replace(' ', '')
        new_price = float(price_str)
        PRICES[key] = new_price
        save_prices(PRICES)
        
        await message.answer(f"✅ Narx muvaffaqiyatli saqlandi!")
        await show_settings_menu(message)
        await state.set_state(None)
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
