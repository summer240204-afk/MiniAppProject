import os
import json
import sqlite3
import html
import os


import telebot
from telebot import types


BOT_TOKEN = "8818731291:AAG98FHdORTQIxKhp1nBcmQNvc8QR3JQ_YA"
WEBAPP_URL = "https://effortless-gnome-87fcbf.netlify.app"

ADMIN_ID = 1244731064

DEFAULT_SPONSOR_CHANNEL = "@rrrteww"
DEFAULT_SPONSOR_LINK = "https://t.me/rrrteww"

DATABASE_NAME = "database.db"

bot = telebot.TeleBot(BOT_TOKEN)

admin_states = {}


# =========================
# БАЗА ДАННЫХ
# =========================

def db_connect():
    return sqlite3.connect(DATABASE_NAME)


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column[1] == column_name:
            return True

    return False


def init_db():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsor_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            link TEXT NOT NULL,
            title TEXT,
            insert_position INTEGER
        )
    """)

    conn.commit()

    if not column_exists(cursor, "links", "title"):
        cursor.execute("ALTER TABLE links ADD COLUMN title TEXT")

    if not column_exists(cursor, "sponsor_channels", "title"):
        cursor.execute("ALTER TABLE sponsor_channels ADD COLUMN title TEXT")

    if not column_exists(cursor, "sponsor_channels", "insert_position"):
        cursor.execute("ALTER TABLE sponsor_channels ADD COLUMN insert_position INTEGER")

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sponsor_channels")
    channels_count = cursor.fetchone()[0]

    if channels_count == 0:
        cursor.execute("""
            INSERT INTO sponsor_channels (channel, link, title, insert_position)
            VALUES (?, ?, ?, ?)
        """, (
            DEFAULT_SPONSOR_CHANNEL,
            DEFAULT_SPONSOR_LINK,
            f"🔥 {DEFAULT_SPONSOR_CHANNEL}",
            None
        ))

        conn.commit()

    conn.close()


def add_user_to_db(user_id, username, first_name):
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (user_id, username, first_name))

    conn.commit()
    conn.close()


def get_users():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    conn.close()

    return [user[0] for user in users]


def get_users_count():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()

    return count


def add_link(title, url):
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO links (title, url)
        VALUES (?, ?)
    """, (title, url))

    conn.commit()
    conn.close()


def get_links():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, url FROM links ORDER BY id ASC")
    links = cursor.fetchall()

    conn.close()

    return links


def clear_links():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM links")

    conn.commit()
    conn.close()


def add_sponsor_channel(channel, link, title=None, insert_position=None):
    conn = db_connect()
    cursor = conn.cursor()

    if title is None or title.strip() == "":
        title = f"🔥 {channel}"

    cursor.execute("""
        INSERT INTO sponsor_channels (channel, link, title, insert_position)
        VALUES (?, ?, ?, ?)
    """, (channel, link, title, insert_position))

    conn.commit()
    conn.close()


def get_sponsor_channels():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, channel, link, title, insert_position
        FROM sponsor_channels
        ORDER BY id ASC
    """)

    channels = cursor.fetchall()

    conn.close()

    return channels


def clear_sponsor_channels():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sponsor_channels")

    conn.commit()
    conn.close()


# =========================
# РАБОТА С КЛИКАБЕЛЬНЫМИ ССЫЛКАМИ
# =========================

def utf16_index_to_py_index(text, utf16_index):
    encoded = text.encode("utf-16-le")
    sliced = encoded[:utf16_index * 2]

    try:
        return len(sliced.decode("utf-16-le"))
    except UnicodeDecodeError:
        return len(sliced.decode("utf-16-le", errors="ignore"))


def extract_clickable_links_from_message(message):
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    result = []

    lines = text.splitlines()
    current_offset = 0

    for line in lines:
        clean_line = line.strip()

        if not clean_line:
            current_offset += len(line) + 1
            continue

        line_start = current_offset
        line_end = current_offset + len(line)

        found_url = None

        for entity in entities:
            entity_start = utf16_index_to_py_index(text, entity.offset)
            entity_end = utf16_index_to_py_index(text, entity.offset + entity.length)

            if entity_start >= line_start and entity_end <= line_end:
                if entity.type == "text_link":
                    found_url = entity.url
                    break

                if entity.type == "url":
                    found_url = text[entity_start:entity_end]
                    break

        if found_url:
            result.append({
                "title": clean_line,
                "url": found_url
            })

        current_offset += len(line) + 1

    return result


def build_clickable_links_text(links):
    lines = []

    for item in links:
        title = html.escape(str(item["title"]))
        url = html.escape(str(item["url"]), quote=True)

        lines.append(f'<a href="{url}">{title}</a>')

    return "\n".join(lines)


def get_final_links_with_sponsors():
    main_links = []

    for link_id, title, url in get_links():
        if not title:
            title = url

        main_links.append({
            "title": title,
            "url": url
        })

    sponsor_links = []

    for channel_id, channel, link, title, insert_position in get_sponsor_channels():
        if not title:
            title = f"🔥 {channel}"

        sponsor_links.append({
            "title": title,
            "url": link,
            "position": insert_position
        })

    final_links = main_links.copy()

    sponsors_with_position = []
    sponsors_without_position = []

    for sponsor in sponsor_links:
        if sponsor["position"]:
            sponsors_with_position.append(sponsor)
        else:
            sponsors_without_position.append(sponsor)

    sponsors_with_position.sort(key=lambda item: item["position"])

    offset = 0

    for sponsor in sponsors_with_position:
        position = sponsor["position"]
        insert_index = position - 1 + offset

        if insert_index < 0:
            insert_index = 0

        if insert_index > len(final_links):
            insert_index = len(final_links)

        final_links.insert(insert_index, {
            "title": sponsor["title"],
            "url": sponsor["url"]
        })

        offset += 1

    for sponsor in sponsors_without_position:
        final_links.append({
            "title": sponsor["title"],
            "url": sponsor["url"]
        })

    return final_links


def send_long_html_message(chat_id, text, reply_markup=None):
    max_length = 3900

    if len(text) <= max_length:
        bot.send_message(
            chat_id,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return

    parts = []
    current_part = ""

    for line in text.splitlines():
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line
        else:
            if current_part:
                current_part += "\n" + line
            else:
                current_part = line

    if current_part:
        parts.append(current_part)

    for index, part in enumerate(parts):
        markup = reply_markup if index == len(parts) - 1 else None

        bot.send_message(
            chat_id,
            part,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=markup
        )


# =========================
# КЛАВИАТУРЫ
# =========================

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(types.KeyboardButton("📢 Сделать рассылку"))
    markup.add(types.KeyboardButton("📥 Импорт ссылок"))
    markup.add(types.KeyboardButton("⚙️ Каналы с проверкой"))
    markup.add(types.KeyboardButton("📋 Показать ссылки"))
    markup.add(types.KeyboardButton("📊 Статистика"))
    markup.add(types.KeyboardButton("🗑 Очистить список ссылок"))
    markup.add(types.KeyboardButton("♻️ Сбросить проверочные каналы"))
    markup.add(types.KeyboardButton("❌ Отмена"))

    return markup


def sponsor_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)

    channels = get_sponsor_channels()

    for channel_id, channel, link, title, insert_position in channels:
        markup.add(
            types.InlineKeyboardButton(
                text=f"📢 Подписаться на {channel}",
                url=link
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            text="✅ Проверить подписку",
            callback_data="check_subscription"
        )
    )

    return markup


def webapp_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    web_app = types.WebAppInfo(WEBAPP_URL)

    button = types.KeyboardButton(
        text="📡 Открыть Mini App",
        web_app=web_app
    )

    markup.add(button)

    return markup


# =========================
# ПРОВЕРКА ПОДПИСКИ
# =========================

def is_subscribed(user_id):
    channels = get_sponsor_channels()

    if not channels:
        return True

    for channel_id, channel, link, title, insert_position in channels:
        try:
            member = bot.get_chat_member(channel, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False

        except Exception as error:
            print("Ошибка проверки подписки:", error)
            return False

    return True


# =========================
# ОСНОВНЫЕ КОМАНДЫ
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    add_user_to_db(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    text = (
        "👋 Привет!\n\n"
        "Этот бот помогает добавить функции, чтобы видеть действия пользователей\n\n"
        "Доступные разделы:\n"
        "👀 Ник активного чата — под ником человека видно, с кем он сейчас в переписке\n"
        "🚪 Вход в ваш чат — приходит сверху экрана телефона Пуш-уведомление, что пользователь открыл чат с вами\n"
        "🗑️ Удалённое сообщение — приходит сверху экрана телефона Пуш-уведомление, с информацией об удалённом тексте и времени удаления\n"
        "⌨️ Живой набор текста — видно, как человек набирает и стирает текст в реальном времени\n\n"
        "Чтобы открыть Mini App, нужно подписаться на спонсора и пройти проверку подписки."
    )

    if is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            text + "\n\n✅ Подписка подтверждена. Mini App доступен.",
            reply_markup=webapp_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            text + "\n\n👇 Сначала подпишитесь на спонсоров:",
            reply_markup=sponsor_keyboard()
        )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ Помощь\n\n"
        "Доступные команды:\n"
        "/start — открыть приветствие\n"
        "/help — помощь\n"
        "/access — проверить доступ к Mini App\n"
        "/admin — админ-панель\n\n"
        "Для доступа к Mini App необходимо быть подписанным на каналы-спонсоры."
    )


@bot.message_handler(commands=["access"])
def access_command(message):
    add_user_to_db(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    if is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "✅ Подписка подтверждена. Mini App доступен:",
            reply_markup=webapp_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Подписка не найдена.\n\n"
            "Подпишитесь на спонсоров и нажмите кнопку проверки.",
            reply_markup=sponsor_keyboard()
        )


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ У тебя нет доступа к админ-панели.")
        return

    bot.send_message(
        message.chat.id,
        "🔐 Админ-панель открыта.\n\nВыбери действие:",
        reply_markup=admin_keyboard()
    )


# =========================
# CALLBACK ПРОВЕРКИ ПОДПИСКИ
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

    add_user_to_db(
        call.from_user.id,
        call.from_user.username,
        call.from_user.first_name
    )

    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "Подписка подтверждена ✅")

        bot.send_message(
            call.message.chat.id,
            "✅ Отлично! Подписка подтверждена.\n\n"
            "Теперь вы можете открыть Mini App:",
            reply_markup=webapp_keyboard()
        )
    else:
        bot.answer_callback_query(
            call.id,
            "Подписка не найдена",
            show_alert=True
        )

        bot.send_message(
            call.message.chat.id,
            "❌ Пока подписка не найдена.\n\n"
            "Подпишитесь на все каналы и нажмите «Проверить подписку».",
            reply_markup=sponsor_keyboard()
        )


# =========================
# ОБРАБОТКА СОСТОЯНИЙ АДМИНА
# =========================

@bot.message_handler(
    content_types=["text", "photo", "video", "document", "sticker", "animation", "voice"],
    func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in admin_states
)
def handle_admin_state(message):
    state = admin_states.get(message.from_user.id)

    if message.content_type == "text" and message.text == "❌ Отмена":
        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            "❌ Действие отменено.",
            reply_markup=admin_keyboard()
        )
        return

    if state == "waiting_broadcast":
        users = get_users()

        success = 0
        failed = 0

        bot.send_message(message.chat.id, "📢 Рассылка началась...")

        for user_id in users:
            try:
                bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
                success += 1
            except Exception:
                failed += 1

        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            f"✅ Рассылка завершена.\n\n"
            f"Успешно: {success}\n"
            f"Ошибок: {failed}",
            reply_markup=admin_keyboard()
        )

        return

    if state == "waiting_links_import":
        if message.content_type != "text":
            bot.send_message(
                message.chat.id,
                "❌ Нужно отправить именно текст с кликабельными ссылками.",
                reply_markup=admin_keyboard()
            )
            return

        imported_links = extract_clickable_links_from_message(message)

        if not imported_links:
            bot.send_message(
                message.chat.id,
                "❌ Я не нашла кликабельные ссылки.\n\n"
                "Важно: текст должен быть именно кликабельным.\n"
                "То есть ты нажимаешь на строку — и открывается канал.\n\n"
                "Пример правильного вида:\n"
                "🛍️ Вб дарит бесплатно\n"
                "💅 Трендовый маникюр\n"
                "📳 Рекко",
                reply_markup=admin_keyboard()
            )
            return

        clear_links()

        added = 0

        for item in imported_links:
            add_link(item["title"], item["url"])
            added += 1

        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            f"✅ Импорт завершён.\n\n"
            f"Добавлено кликабельных ссылок: {added}",
            reply_markup=admin_keyboard()
        )

        return

    if state == "waiting_sponsor_channels":
        if message.content_type != "text":
            bot.send_message(
                message.chat.id,
                "❌ Нужно отправить текст со списком каналов.",
                reply_markup=admin_keyboard()
            )
            return

        lines = message.text.splitlines()

        added = 0

        for line in lines:
            line = line.strip()

            if not line:
                continue

            parts = [part.strip() for part in line.split("|")]

            channel = None
            link = None
            title = None
            insert_position = None

            if len(parts) == 1:
                channel = parts[0]
                link = f"https://t.me/{channel.replace('@', '')}"
                title = f"🔥 {channel}"

            elif len(parts) == 2:
                channel = parts[0]
                link = parts[1]
                title = f"🔥 {channel}"

            elif len(parts) == 3:
                channel = parts[0]
                link = parts[1]
                title = parts[2]

            elif len(parts) >= 4:
                channel = parts[0]
                link = parts[1]
                title = parts[2]

                try:
                    insert_position = int(parts[3])
                except Exception:
                    insert_position = None

            if (
                isinstance(channel, str)
                and isinstance(link, str)
                and channel.startswith("@")
                and link.startswith("http")
            ):
                add_sponsor_channel(channel, link, title, insert_position)
                added += 1

        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            f"✅ Проверочные каналы добавлены.\n\n"
            f"Добавлено: {added}\n\n"
            "Если ты указала позицию, канал вставится внутрь списка ссылок.",
            reply_markup=admin_keyboard()
        )

        return


# =========================
# КНОПКИ АДМИН-ПАНЕЛИ
# =========================

@bot.message_handler(func=lambda message: message.text == "📢 Сделать рассылку")
def start_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    admin_states[message.from_user.id] = "waiting_broadcast"

    bot.send_message(
        message.chat.id,
        "📢 Отправь сообщение для рассылки.\n\n"
        "Можно отправить текст, фото, видео, документ, стикер или голосовое.\n\n"
        "Для отмены нажми ❌ Отмена.",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "📥 Импорт ссылок")
def import_links_start(message):
    if message.from_user.id != ADMIN_ID:
        return

    admin_states[message.from_user.id] = "waiting_links_import"

    bot.send_message(
        message.chat.id,
        "📥 Отправь список КЛИКАБЕЛЬНЫХ ссылок одним сообщением.\n\n"
        "То есть не так:\n"
        "https://t.me/channel1\n\n"
        "А вот так, чтобы каждая строка уже нажималась:\n\n"
        "🛍️ Вб дарит бесплатно\n"
        "💅 Трендовый маникюр\n"
        "📳 Рекко\n\n"
        "Важно: если строка не кликается у тебя в Telegram, бот тоже не сможет узнать ссылку.\n\n"
        "Для отмены нажми ❌ Отмена.",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "⚙️ Каналы с проверкой")
def sponsor_channels_start(message):
    if message.from_user.id != ADMIN_ID:
        return

    admin_states[message.from_user.id] = "waiting_sponsor_channels"

    bot.send_message(
        message.chat.id,
        "⚙️ Отправь проверочные каналы списком.\n\n"
        "Формат простой:\n"
        "@channel1\n\n"
        "Формат со ссылкой:\n"
        "@channel1 | https://t.me/channel1\n\n"
        "Формат с названием:\n"
        "@channel1 | https://t.me/channel1 | 🔥 Твоя проверочная ссылка\n\n"
        "Формат с названием и местом вставки:\n"
        "@channel1 | https://t.me/channel1 | 🔥 Твоя проверочная ссылка | 21\n\n"
        "Где 21 — это место, куда вставить проверочную ссылку внутри общего списка.\n\n"
        "Если проверочных каналов два:\n"
        "@channel1 | https://t.me/channel1 | 🔥 Проверка 1 | 5\n"
        "@channel2 | https://t.me/channel2 | 🔥 Проверка 2 | 20\n\n"
        "Для отмены нажми ❌ Отмена.",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "📋 Показать ссылки")
def show_links(message):
    if message.from_user.id != ADMIN_ID:
        return

    final_links = get_final_links_with_sponsors()
    channels = get_sponsor_channels()

    if not final_links:
        links_text = "Список ссылок пуст."
    else:
        links_text = build_clickable_links_text(final_links)

    text = "📋 Итоговый список ссылок:\n\n"
    text += links_text

    text += "\n\n📢 Проверочные каналы:\n\n"

    if not channels:
        text += "Список каналов пуст."
    else:
        for channel_id, channel, link, title, insert_position in channels:
            safe_channel = html.escape(str(channel))
            safe_title = html.escape(str(title))
            safe_link = html.escape(str(link))

            text += f"{channel_id}. {safe_channel}\n"
            text += f"Название: {safe_title}\n"
            text += f"Ссылка: {safe_link}\n"

            if insert_position:
                text += f"Место вставки: {insert_position}\n"
            else:
                text += "Место вставки: в конец списка\n"

            text += "\n"

    send_long_html_message(
        message.chat.id,
        text,
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    users_count = get_users_count()
    links_count = len(get_links())
    channels_count = len(get_sponsor_channels())

    bot.send_message(
        message.chat.id,
        "📊 Статистика\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔗 Ссылок: {links_count}\n"
        f"📢 Проверочных каналов: {channels_count}",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "🗑 Очистить список ссылок")
def clear_links_handler(message):
    if message.from_user.id != ADMIN_ID:
        return

    count = len(get_links())

    clear_links()

    bot.send_message(
        message.chat.id,
        f"🗑 Список ссылок очищен.\n\nУдалено ссылок: {count}",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "♻️ Сбросить проверочные каналы")
def reset_sponsor_channels_handler(message):
    if message.from_user.id != ADMIN_ID:
        return

    count = len(get_sponsor_channels())

    clear_sponsor_channels()

    bot.send_message(
        message.chat.id,
        f"♻️ Проверочные каналы сброшены.\n\nУдалено каналов: {count}\n\n"
        "Теперь пользователи смогут открыть Mini App без подписки, "
        "пока ты не добавишь новые каналы.",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def cancel_admin_action(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.from_user.id in admin_states:
        del admin_states[message.from_user.id]

    bot.send_message(
        message.chat.id,
        "❌ Действие отменено.",
        reply_markup=admin_keyboard()
    )


# =========================
# MINI APP DATA
# =========================

@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
    add_user_to_db(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        bot.send_message(message.chat.id, "Ошибка чтения данных из Mini App")
        return

    service = data.get("service", "Не выбрано")
    user = data.get("user", {})

    first_name = user.get("first_name", "Без имени") if user else "Без имени"
    username = user.get("username", "нет username") if user else "нет username"
    user_id = user.get("id", message.from_user.id) if user else message.from_user.id

    client_message = (
        "✅ Запрос принят.\n\n"
        f"Выбранный раздел: {service}\n\n"
        "⏳ Ожидание обработки: 48–56 часов.\n"
        "Пожалуйста, не отписывайтесь от спонсоров до завершения проверки."
    )

    admin_message = (
        "📡 Новый запрос из Mini App\n\n"
        f"Выбранный раздел: {service}\n\n"
        f"Клиент: {first_name}\n"
        f"Username: @{username}\n"
        f"Telegram ID: {user_id}"
    )

    bot.send_message(message.chat.id, client_message)
    bot.send_message(ADMIN_ID, admin_message)

    print(admin_message)


# =========================
# ЗАПУСК
# =========================

try:
    bot.set_my_commands([
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("access", "Проверить доступ к Mini App"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("admin", "Админ-панель")
    ])
except Exception as error:
    print("Не удалось установить команды бота:", error)


init_db()

print("Бот запущен")

bot.infinity_polling(skip_pending=True)