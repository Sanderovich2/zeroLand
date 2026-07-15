import telebot
from telebot import types
import json
import time
import threading

BOT_TOKEN = "ПОМЕНЯЙ_НА_СВОЙ"
ADMIN_ID = ПОМЕНЯЙ_НА_СВОЙ

global bot_status
bot = telebot.TeleBot(BOT_TOKEN)

_request_lock = threading.Lock()
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 0.35

def ratelimit():
    global _last_request_time
    with _request_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        _last_request_time = time.time()

def safe_send_message(chat_id, text, *args, **kwargs):
    ratelimit()
    return bot.send_message(chat_id, text, *args, **kwargs)

def safe_answer_inline(query_id, results, *args, **kwargs):
    ratelimit()
    return bot.answer_inline_query(query_id, results, *args, **kwargs)

def safe_answer_callback(callback_query_id, text="", *args, **kwargs):
    ratelimit()
    return bot.answer_callback_query(callback_query_id, text=text, *args, **kwargs)

def safe_edit_message_text(text, chat_id=None, message_id=None, *args, **kwargs):
    ratelimit()
    return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, *args, **kwargs)

def safe_delete_message(chat_id, message_id):
    ratelimit()
    return bot.delete_message(chat_id, message_id)


ZERO_LAND = {
    "а": "Δ", "б": "6", "в": "β", "г": "г", "д": "д", "е": "ε", "ё": "ё", "ж": "ж",
    "з": "3", "и": "u", "й": "й", "к": "κ", "л": "ʌ", "м": "м", "н": "н", "о": "ο",
    "п": "π", "р": "ρ", "с": "c", "т": "τ", "у": "y", "ф": "φ", "х": "x", "ц": "ц",
    "ч": "ч", "ш": "ш", "щ": "щ", "э": "э", "ю": "ю", "я": "λ",
    "А": "Δ", "Б": "6", "В": "Β", "Г": "Γ", "Д": "Δ", "Е": "Е", "Ё": "Ё", "Ж": "Ж",
    "З": "3", "И": "U", "Й": "Й", "К": "Κ", "Л": "Λ", "М": "Μ", "Н": "Ν", "О": "Ο",
    "П": "Π", "Р": "Ρ", "С": "C", "Т": "Τ", "У": "Y", "Ф": "Φ", "Х": "Χ", "Ц": "Ц",
    "Ч": "Ч", "Ш": "Ш", "Щ": "Щ", "Э": "Э", "Ю": "Ю", "Я": "Λ",
}

def zeroland(text: str):
    result = ""
    for ch in text:
        if ch in ZERO_LAND:
            result += ZERO_LAND[ch]
        else:
            result += ch
    return result

bot_status = {"is_running": True, "is_in_break": False}

def is_bot_available():
    try:
        with open("bot_status.json", "r") as f:
            status = json.load(f)
        return status["is_running"] and not status["is_in_break"]
    except:
        return False

USER_MODES_FILE = "user_modes.json"
_MODES_CACHE = {}
_MODES_LOCK = threading.Lock()

def _load_modes():
    global _MODES_CACHE
    try:
        with open(USER_MODES_FILE, "r") as f:
            _MODES_CACHE = json.load(f)
    except:
        _MODES_CACHE = {}

def _save_modes():
    with open(USER_MODES_FILE, "w") as f:
        json.dump(_MODES_CACHE, f)

_load_modes()

def get_mode(chat_id):
    with _MODES_LOCK:
        return _MODES_CACHE.get(str(chat_id), "normal")

def set_mode(chat_id, mode):
    with _MODES_LOCK:
        _MODES_CACHE[str(chat_id)] = mode
        _save_modes()

def format_text(text, mode):
    converted = zeroland(text)
    if mode == "decorative":
        return zeroland("⟦ ") + converted + zeroland(" ⟧")
    return converted

@bot.message_handler(commands=['start'])
def start(message):
    if is_bot_available():
        username = message.from_user.username or message.from_user.first_name
        text = zeroland("👑 ZERO LAND BOT\n\nПривет, @") + username + zeroland("!\n\nОтправь текст — я переведу его на язык ZeroLand.\n\n⚜ Декоративный режим добавляет оформление: ⟦ пример текста ⟧\n\nInline режим: @zeroland_translatebot твой текст")
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(zeroland("✨ Обычный"), callback_data="normal"))
        keyboard.row(types.InlineKeyboardButton(zeroland("⚜ Декоративный"), callback_data="decorative"))
        keyboard.row(types.InlineKeyboardButton(zeroland("📖 Алфавит"), callback_data="alphabet"))
        
        safe_send_message(message.chat.id, text, reply_markup=keyboard)
    else:
        safe_send_message(message.chat.id, zeroland("⚠️ Бот временно недоступен."))

def normal_callback(call):
    set_mode(call.message.chat.id, "normal")
    safe_answer_callback(call.id, zeroland("✨ Обычный режим включён"))

def decorative_callback(call):
    set_mode(call.message.chat.id, "decorative")
    safe_answer_callback(call.id, zeroland("⚜ Декоративный режим включён"))

def alphabet_callback(call):
    small = [
        "а→Δ", "б→6", "в→β", "г→г", "д→д", "е→ε", "ё→ё", "ж→ж",
        "з→3", "и→u", "й→й", "к→κ", "л→ʌ", "м→м", "н→н", "о→ο",
        "п→π", "р→ρ", "с→c", "т→τ", "у→y", "ф→φ", "х→x", "ц→ц",
        "ч→ч", "ш→ш", "щ→щ", "э→э", "ю→ю", "я→λ",
    ]
    capital = [
        "А→Δ", "Б→6", "В→Β", "Г→Γ", "Д→Δ", "Е→Е", "Ё→Ё", "Ж→Ж",
        "З→3", "И→U", "Й→Й", "К→Κ", "Л→Λ", "М→Μ", "Н→Ν", "О→Ο",
        "П→Π", "Р→Ρ", "С→C", "Т→Τ", "У→Y", "Ф→Φ", "Х→Χ", "ЦЦ",
        "Ч→Ч", "Ш→Ш", "Щ→Щ", "Э→Э", "Ю→Ю", "Я→Λ",
    ]
    lines = [
        "Маленькие:",
        "  ".join(small),
        "",
        "Заглавные:",
        "  ".join(capital),
    ]
    text = "\n".join(lines)
    safe_send_message(call.message.chat.id, text)
    safe_answer_callback(call.id, "")

bot.register_callback_query_handler(normal_callback, func=lambda call: call.data == "normal")
bot.register_callback_query_handler(decorative_callback, func=lambda call: call.data == "decorative")
bot.register_callback_query_handler(alphabet_callback, func=lambda call: call.data == "alphabet")

@bot.message_handler(commands=['normal'])
def cmd_normal(message):
    set_mode(message.chat.id, "normal")
    safe_send_message(message.chat.id, zeroland("✨ Обычный режим включён"))

@bot.message_handler(commands=['decorative'])
def cmd_decorative(message):
    set_mode(message.chat.id, "decorative")
    safe_send_message(message.chat.id, zeroland("⚜ Декоративный режим включён"))

@bot.message_handler(commands=['alphabet'])
def cmd_alphabet(message):
    small = [
        "а→Δ", "б→6", "в→β", "г→г", "д→д", "е→ε", "ё→ё", "ж→ж",
        "з→3", "и→u", "й→й", "к→κ", "л→ʌ", "м→м", "н→н", "о→ο",
        "п→π", "р→ρ", "с→c", "т→τ", "у→y", "ф→φ", "х→x", "ц→ц",
        "ч→ч", "ш→ш", "щ→щ", "э→э", "ю→ю", "я→λ",
    ]
    capital = [
        "А→Δ", "Б→6", "В→Β", "Г→Γ", "Д→Δ", "Е→Е", "Ё→Ё", "Ж→Ж",
        "З→3", "И→U", "Й→Й", "К→Κ", "Л→Λ", "М→Μ", "Н→Ν", "О→Ο",
        "П→Π", "Р→Ρ", "С→C", "Т→Τ", "У→Y", "Ф→Φ", "Х→Χ", "ЦЦ",
        "Ч→Ч", "Ш→Ш", "Щ→Щ", "Э→Э", "Ю→Ю", "Я→Λ",
    ]
    lines = [
        "Маленькие:",
        "  ".join(small),
        "",
        "Заглавные:",
        "  ".join(capital),
    ]
    safe_send_message(message.chat.id, "\n".join(lines))

@bot.message_handler(content_types=['text'], func=lambda message: not message.text.startswith('/'))
def message_handler(message):
    if not is_bot_available():
        return
    text = message.text.strip()
    if text.startswith('/'):
        return
    result = format_text(text, get_mode(message.chat.id))
    safe_send_message(message.chat.id, result)

@bot.inline_handler(lambda query: True)
def inline_query(query):
    if not is_bot_available():
        return
   
    query_text = query.query.strip()
   
    if query_text.startswith('@'):
        mention, text = query_text.split('@', 1)
        text = text.strip()
        if not text:
            text = mention
            mention = ""
    else:
        mention = ""
        text = query_text

    if not text:
        content = mention + text
        if not content:
            safe_answer_inline(query.id, [], cache_time=5)
            return
        results = [types.InlineQueryResultArticle("1", "ZeroLand", 
                  input_message_content=types.InputTextMessageContent(content))]
        safe_answer_inline(query.id, results, cache_time=5)
        return

    normal_result = types.InlineQueryResultArticle(
        "1", zeroland("✨ Обычный"), 
        input_message_content=types.InputTextMessageContent(mention + zeroland(text))
    )
    decorative_result = types.InlineQueryResultArticle(
        "2", zeroland("⚜ Декоративный"), 
        input_message_content=types.InputTextMessageContent(mention + zeroland("⟦ ") + zeroland(text) + zeroland(" ⟧"))
    )

    safe_answer_inline(query.id, [normal_result, decorative_result], cache_time=5)

@bot.message_handler(commands=['help'])
def help_command(message):
    if is_bot_available():
        text = zeroland("👑 ZERO LAND HELP\n\n/start — Главное меню\n\n/admin_panel — Админ-панель\n\n/myid — Твой ID\n\n/help — Эта помощь\n\n⚜ Декоративный режим добавляет скобки ⟦ ⟧")
        safe_send_message(message.chat.id, text)

@bot.message_handler(commands=['myid'])
def myid(message):
    text = f"Твой ID: {message.from_user.id}\nUsername: @{message.from_user.username}"
    safe_send_message(message.chat.id, text)

@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    user_id = int(message.from_user.id)
    if user_id != ADMIN_ID:
        safe_send_message(message.chat.id, zeroland("❌ Только админ может использовать эту команду."))
        return
   
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton(zeroland("⏸ Перерыв"), callback_data="start_break"))
    keyboard.row(types.InlineKeyboardButton(zeroland("▶️ Нет перерыва"), callback_data="end_break"))
    keyboard.row(types.InlineKeyboardButton(zeroland("📤 Отправить всем"), callback_data="send_message"))
    keyboard.row(types.InlineKeyboardButton(zeroland("🔄 Обновить бота"), callback_data="update_bot"))
   
    safe_send_message(message.chat.id, zeroland("👑 ZERO LAND ADMIN PANEL\n\nВыбери действие:"), reply_markup=keyboard)

def start_break(call):
    global bot_status
    bot_status["is_running"] = False
    bot_status["is_in_break"] = True
    with open("bot_status.json", "w") as f:
        json.dump(bot_status, f)
    safe_answer_callback(call.id, zeroland("⏸ Перерыв включён — бот недоступен для всех"))

def end_break(call):
    global bot_status
    bot_status["is_running"] = True
    bot_status["is_in_break"] = False
    with open("bot_status.json", "w") as f:
        json.dump(bot_status, f)
    safe_answer_callback(call.id, zeroland("▶️ Перерыв окончен — бот доступен всем"))

def send_message_callback(call):
    safe_edit_message_text(zeroland("📤 Введи сообщение для ВСЕХ:"), call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, send_message_handler)

def update_bot_callback(call):
    safe_edit_message_text(zeroland("🔄 Введи новый код бота:"), call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, update_bot_handler)

bot.register_callback_query_handler(start_break, func=lambda call: call.data == "start_break")
bot.register_callback_query_handler(end_break, func=lambda call: call.data == "end_break")
bot.register_callback_query_handler(send_message_callback, func=lambda call: call.data == "send_message")
bot.register_callback_query_handler(update_bot_callback, func=lambda call: call.data == "update_bot")

def send_message_handler(message):
    text = message.text
   
    global bot_status
    bot_status["is_running"] = False
    bot_status["is_in_break"] = False
    with open("bot_status.json", "w") as f:
        json.dump(bot_status, f)
   
    safe_send_message(message.chat.id, zeroland("⏸ Бот остановлен для отправки сообщения всем"))
   
    try:
        for update in bot.get_updates():
            if update.message and update.message.chat.type in ["private", "group", "supergroup"]:
                try:
                    safe_send_message(update.message.chat.id, zeroland(text))
                except:
                    pass
    except:
        pass
   
    bot_status["is_running"] = True
    with open("bot_status.json", "w") as f:
        json.dump(bot_status, f)
    safe_send_message(message.chat.id, zeroland("✅ Сообщение отправлено всем! Бот снова доступен."))
    safe_delete_message(message.chat.id, message.message_id)

def update_bot_handler(message):
    new_code = message.text
    with open("bot.py", "w") as f:
        f.write(new_code)
    safe_send_message(message.chat.id, zeroland("✅ Бот обновлён (полностью доступен теперь)!"))
    safe_delete_message(message.chat.id, message.message_id)

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True, interval=0.5)
    except Exception as e:
        print(f"Бот остановлен: {e}")
        with open("bot_status.json", "w") as f:
            json.dump({"is_running": False, "is_in_break": False}, f)