import json
import telebot
from telebot import types


BOT_TOKEN = "8818731291:AAG98FHdORTQIxKhp1nBcmQNvc8QR3JQ_YA"
WEBAPP_URL = "https://effortless-gnome-87fcbf.netlify.app"

ADMIN_ID = 1244731064

SPONSOR_CHANNEL = "@rrrteww"
SPONSOR_LINK = "https://t.me/rrrteww"


bot = telebot.TeleBot(BOT_TOKEN)


def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(SPONSOR_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as error:
        print("Ошибка проверки подписки:", error)
        return False


def sponsor_keyboard():
    markup = types.InlineKeyboardMarkup()

    subscribe_btn = types.InlineKeyboardButton(
        text="📢 Подписаться на спонсора",
        url=SPONSOR_LINK
    )

    check_btn = types.InlineKeyboardButton(
        text="✅ Проверить подписку",
        callback_data="check_subscription"
    )

    markup.add(subscribe_btn)
    markup.add(check_btn)

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


@bot.message_handler(commands=["start"])
def start(message):
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
            text + "\n\n👇 Сначала подпишитесь на спонсора:",
            reply_markup=sponsor_keyboard()
        )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ Помощь\n\n"
        "Бот показывает разделы Mini App по теме видимых действий в Telegram.\n\n"
        "Доступные команды:\n"
        "/start — открыть приветствие\n"
        "/help — помощь\n"
        "/access — проверить доступ к Mini App\n\n"
        "Для доступа необходимо быть подписанным на канал-спонсор."
    )


@bot.message_handler(commands=["access"])
def access_command(message):
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
            "Подпишитесь на спонсора и нажмите кнопку проверки.",
            reply_markup=sponsor_keyboard()
        )


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

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
            "Подпишитесь на спонсора и нажмите «Проверить подписку».",
            reply_markup=sponsor_keyboard()
        )


@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
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
        f"Выбранное действие: {service}\n\n"
        "⏳ Ожидание обработки: 48–56 часов.\n"
        "Пожалуйста, не отписывайтесь от спонсоров до завершения проверки."
    )

    admin_message = (
        "📡 Новый запрос из Mini App\n\n"
        f"Тема: Действия собеседника\n"
        f"Выбранное действие: {service}\n\n"
        f"Клиент: {first_name}\n"
        f"Username: @{username}\n"
        f"Telegram ID: {user_id}"
    )

    bot.send_message(message.chat.id, client_message)
    bot.send_message(ADMIN_ID, admin_message)

    print(admin_message)


bot.set_my_commands([
    types.BotCommand("start", "Запустить бота"),
    types.BotCommand("access", "Проверить доступ к Mini App"),
    types.BotCommand("help", "Помощь")
])


bot.infinity_polling(skip_pending=True)