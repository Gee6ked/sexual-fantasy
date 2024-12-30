import sqlite3
import telebot
from telebot import types
import time
import logging
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (Рекомендуется хранить его в переменной окружения для безопасности)
BOT_TOKEN = '7746429600:AAEYKOvtL55TdNmJy21Cm-fUtBstKmOtc0E'
bot = telebot.TeleBot(BOT_TOKEN)

# База данных
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы пользователей с необходимыми полями
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 100,
    referrals_count INTEGER DEFAULT 0,
    usdt_withdrawn REAL DEFAULT 0,
    last_reward_time INTEGER DEFAULT 0,
    completed_tasks TEXT DEFAULT ""
)''')
conn.commit()

# Проверка и добавление необходимых столбцов
def add_missing_columns():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_reward_time INTEGER DEFAULT 0")
        logger.info("Столбец 'last_reward_time' успешно добавлен.")
    except sqlite3.OperationalError:
        logger.info("Столбец 'last_reward_time' уже существует.")
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN completed_tasks TEXT DEFAULT ''")
        logger.info("Столбец 'completed_tasks' успешно добавлен.")
    except sqlite3.OperationalError:
        logger.info("Столбец 'completed_tasks' уже существует.")
    
    conn.commit()

add_missing_columns()

# Курс обмена Jarli -> USDT
EXCHANGE_RATE = 0.001  # 1000 Jarli = 1 USDT

# Задержка для сбора награды (в секундах)
REWARD_COOLDOWN = 3 * 60 * 60  # 3 часа

# Список заданий с реальными ссылками
tasks = {
    "instagram": {"name": "Instagram", "url": "https://www.instagram.com/your_instagram", "reward": 10},
    "telegram": {"name": "Telegram", "url": "https://t.me/Jarsetinfo", "reward": 10},
    "twitter": {"name": "Twitter", "url": "https://twitter.com/your_twitter", "reward": 10}
}

# Функция добавления пользователя
def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

# Функция для главного меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    profile_button = types.KeyboardButton("👤 Профиль")
    referral_button = types.KeyboardButton("🔗 Реферальная система")
    exchange_button = types.KeyboardButton("💱 Обменник")
    markup.add(profile_button, referral_button, exchange_button)
    return markup

# Функция для клавиатуры в профиле
def profile_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    store_button = types.KeyboardButton("🛒 Магазин")
    deposit_button = types.KeyboardButton("💵 Пополнить баланс")  # Добавляем кнопку
    tasks_button = types.KeyboardButton("📋 Задания")
    collect_reward_button = types.KeyboardButton("🎁 Награда")
    back_button = types.KeyboardButton("🔙 Назад")
    markup.add(store_button, deposit_button, tasks_button, collect_reward_button)
    markup.add(back_button)
    return markup


# Функция для клавиатуры магазина
def store_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    premium_status = types.KeyboardButton("🛡️ Статус Премиум — 2.99 USDT")
    private_tasks = types.KeyboardButton("📂 Доступ к приватным заданиям — 2500 Jarli")
    back_button = types.KeyboardButton("🔙 Назад")
    markup.add(premium_status, private_tasks, back_button)
    return markup

# Функция для кнопок заданий
def task_buttons(task_key, task_info, is_completed):
    markup = types.InlineKeyboardMarkup()
    if not is_completed:
        markup.add(
            types.InlineKeyboardButton("🔗 Подписаться", url=task_info['url']),
            types.InlineKeyboardButton("✅ Выполнил", callback_data=f"done_{task_key}")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{task_key}", callback_game=None)
        )
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoName"
    referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None

    add_user(user_id, username)

    if referrer_id and referrer_id.isdigit():
        referrer_id = int(referrer_id)
        if referrer_id != user_id:
            cursor.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?", (referrer_id,))
            cursor.execute("UPDATE users SET balance = balance + 50 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            bot.send_message(referrer_id, f"🎉 Ваш друг {username} зарегистрировался через вашу ссылку!\n💰 Вам начислено **50 Jarli**.", parse_mode="Markdown")
    
    bot.send_message(user_id, "*Добро пожаловать!* Выберите опцию:", reply_markup=main_menu(), parse_mode="Markdown")

# Обработчик кнопки "👤 Профиль"
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT username, balance, referrals_count, usdt_withdrawn, last_reward_time, completed_tasks FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        username, balance, referrals_count, usdt_withdrawn, last_reward_time, completed_tasks = user_data
        usdt_balance = balance * EXCHANGE_RATE

        bot.send_message(
            user_id,
            f"👤 **Профиль**\n\n"
            f"👥 **Имя:** {username}\n"
            f"💰 **Баланс Jarli:** {balance:.2f} Jarli\n"
            f"💵 **Эквивалент в USDT:** {usdt_balance:.6f} USDT\n"
            f"📈 **Приглашенные друзья:** {referrals_count}\n"
            f"📤 **Выведено:** {usdt_withdrawn:.6f} USDT\n",
            reply_markup=profile_menu(),
            parse_mode="Markdown"
        )

# Обработчик кнопки "🔗 Реферальная система"
@bot.message_handler(func=lambda message: message.text == "🔗 Реферальная система")
def referral_system(message):
    user_id = message.from_user.id
    cursor.execute("SELECT referrals_count FROM users WHERE user_id = ?", (user_id,))
    referrals_count = cursor.fetchone()[0]
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(
        user_id,
        f"🔗 **Реферальная система**\n\n"
        f"👥 **Приглашенные друзья:** {referrals_count}\n\n"
        f"💡 **Приглашайте друзей с помощью ссылки:**\n"
        f"`{referral_link}`\n\n"
        f"🎁 **За каждого друга вы получаете 50 Jarli!**",
        parse_mode="Markdown"
    )

# Обработчик кнопки "💱 Обменник"
@bot.message_handler(func=lambda message: message.text == "💱 Обменник")
def exchange(message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    progress = (balance / 10000) * 100  # Прогресс до обмена в процентах (цель - 10,000 Jarli)

    if balance < 10000:
        filled_blocks = int(progress // 10)
        empty_blocks = 10 - filled_blocks
        progress_bar = "🟩" * filled_blocks + "⬜" * empty_blocks

        bot.send_message(
            user_id,
            f"📊 **Ваш прогресс к первому обмену**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📈 *Текущий баланс:* {balance:.2f} Jarli\n"
            f"🎯 *Цель для обмена:* 10,000 Jarli\n"
            f"📉 *Прогресс:* {progress_bar} {progress:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Для доступа к обменнику ваш баланс должен быть не менее 10,000 Jarli.*",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            user_id,
            f"🎉 **Поздравляем!** У вас достаточно средств для обмена.\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Баланс:* {balance:.2f} Jarli\n"
            f"💵 *Эквивалент в USDT:* {balance * EXCHANGE_RATE:.6f} USDT\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💱 *Сколько Jarli вы хотите обменять?*",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(message, exchange_jarli)

def exchange_jarli(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text.strip())
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()[0]

        if amount <= 0:
            bot.send_message(user_id, "⚠️ Введите положительное число.", parse_mode="Markdown")
        elif amount > balance:
            bot.send_message(user_id, f"⚠️ Недостаточно средств. Ваш баланс: {balance:.2f} Jarli.", parse_mode="Markdown")
        else:
            usdt_amount = amount * EXCHANGE_RATE
            new_balance = balance - amount
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.send_message(user_id, f"✅ Вы успешно обменяли {amount:.2f} Jarli на {usdt_amount:.6f} USDT.", parse_mode="Markdown")
    except ValueError:
        bot.send_message(user_id, "⚠️ Введите корректное число.", parse_mode="Markdown")

# Обработчик кнопки "🛒 Магазин"
@bot.message_handler(func=lambda message: message.text == "🛒 Магазин")
def store(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        f"🛒 **Магазин товаров**\n\n"
        f"🛡️ **Статус Премиум** — 2.99 USDT\n"
        f"    🎉 *Доступ к эксклюзивным функциям.*\n\n"
        f"📂 **Доступ к приватным заданиям** — 2500 Jarli\n"
        f"    💼 *Получайте уникальные задания для дополнительного заработка.*\n\n"
        f"🔙 *Выберите товар, который хотите приобрести:*",
        reply_markup=store_menu(),
        parse_mode="Markdown"
    )

# Обработчик покупки товаров
@bot.message_handler(func=lambda message: message.text.startswith("🛡️") or message.text.startswith("📂"))
def buy_item(message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if "Статус Премиум" in message.text:
        price_usdt = 2.99
        jarli_needed = price_usdt / EXCHANGE_RATE  # Конвертация USDT в Jarli
        if balance >= jarli_needed:
            new_balance = balance - jarli_needed
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.send_message(user_id, "✅ Вы успешно приобрели **Статус Премиум**! Наслаждайтесь эксклюзивными функциями.", parse_mode="Markdown")
        else:
            bot.send_message(user_id, f"⚠️ Недостаточно средств. Вам нужно **{jarli_needed:.2f} Jarli** для покупки **Статус Премиум**.", parse_mode="Markdown")

    elif "Доступ к приватным заданиям" in message.text:
        price_jarli = 2500
        if balance >= price_jarli:
            new_balance = balance - price_jarli
            # Здесь можно добавить логику предоставления доступа к дополнительным заданиям
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.send_message(user_id, "✅ Вы успешно приобрели **Доступ к приватным заданиям**! Получайте дополнительные задания.", parse_mode="Markdown")
        else:
            bot.send_message(user_id, f"⚠️ Недостаточно средств. Вам нужно **{price_jarli} Jarli** для покупки **Доступ к приватным заданиям**.", parse_mode="Markdown")

# Обработчик кнопки "🔙 Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад" or message.text == "Назад")
def back_to_main_menu(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "🔙 Вы вернулись в главное меню. Выберите опцию:", reply_markup=main_menu(), parse_mode="Markdown")

# Обработчик кнопки "📋 Задания"
@bot.message_handler(func=lambda message: message.text == "📋 Задания")
def show_tasks(message):
    user_id = message.from_user.id
    cursor.execute("SELECT completed_tasks FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    completed_tasks = data[0].split(",") if data and data[0] else []

    if not tasks:
        bot.send_message(user_id, "📋 **Сейчас нет доступных заданий.**", parse_mode="Markdown")
        return

    response = "*📋 Доступные задания:*\n\n"
    for idx, (task_key, task_info) in enumerate(tasks.items(), start=1):
        is_completed = task_key in completed_tasks
        status = "✅ Выполнено" if is_completed else "❌ Не выполнено"
        response += f"{idx}. *{task_info['name']}* — {status}\n"
    response += "\n🎯 *Выполняйте задания, чтобы заработать 10 Jarli за каждое!*"

    bot.send_message(
        user_id,
        response,
        parse_mode="Markdown"
    )

    # Отправляем кнопки для каждого задания
    for task_key, task_info in tasks.items():
        is_completed = task_key in completed_tasks
        bot.send_message(
            user_id,
            f"**{task_info['name']}**",
            reply_markup=task_buttons(task_key, task_info, is_completed),
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def confirm_task_completed(call):
    user_id = call.from_user.id
    task_id = call.data.split("_")[1]

    cursor.execute("SELECT balance, completed_tasks FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        bot.answer_callback_query(call.id, "⚠️ Ошибка доступа к данным пользователя.")
        return
    balance, completed_tasks = data
    completed_tasks = completed_tasks.split(",") if completed_tasks else []

    if task_id == "telegram":
        chat_id = "@Jarsetinfo"  # Замените на ваш канал
        try:
            status = bot.get_chat_member(chat_id, user_id).status
            if status in ["member", "administrator", "creator"]:
                if task_id not in completed_tasks:
                    new_balance = balance + tasks[task_id]['reward']
                    completed_tasks.append(task_id)
                    cursor.execute(
                        "UPDATE users SET balance = ?, completed_tasks = ? WHERE user_id = ?",
                        (new_balance, ",".join(completed_tasks), user_id)
                    )
                    conn.commit()
                    bot.answer_callback_query(call.id, "✅ Подписка подтверждена! Вы получили награду.")
                    bot.send_message(user_id, f"🎉 Спасибо за подписку! Ваш новый баланс: {new_balance} Jarli.")
                else:
                    bot.answer_callback_query(call.id, "⚠️ Вы уже выполнили это задание.")
            else:
                bot.answer_callback_query(call.id, "❌ Вы не подписаны на канал.")
        except Exception as e:
            bot.answer_callback_query(call.id, f"⚠️ Ошибка проверки: {e}")
    else:
        # Обработка других заданий (Instagram, Twitter и т.д.)
        ...

# Обработчик кнопки "🎁 Награда"
@bot.message_handler(func=lambda message: message.text == "🎁 Награда")
def collect_reward(message):
    user_id = message.from_user.id
    current_time = int(time.time())

    cursor.execute("SELECT balance, last_reward_time FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        bot.send_message(user_id, "⚠️ Ошибка доступа к данным пользователя.")
        return
    balance, last_reward_time = data

    if current_time - last_reward_time >= REWARD_COOLDOWN:
        # Добавляем награду
        new_balance = balance + 10  # Награда в 10 Jarli
        cursor.execute("UPDATE users SET balance = ?, last_reward_time = ? WHERE user_id = ?", (new_balance, current_time, user_id))
        conn.commit()
        bot.send_message(user_id, f"🎉 Вы получили **10 Jarli**! Теперь у вас **{new_balance:.2f} Jarli**.", parse_mode="Markdown")
    else:
        # Сообщаем, сколько времени осталось
        remaining_time = REWARD_COOLDOWN - (current_time - last_reward_time)
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        bot.send_message(user_id, f"⏳ Вы уже забирали награду. Подождите **{hours} часов, {minutes} минут и {seconds} секунд**.", parse_mode="Markdown")

def create_payment_link(user_id, amount):
    url = f"{CRYPTOBOT_BASE_URL}createInvoice"
    payload = {
        "token": CRYPTOBOT_API_TOKEN,
        "amount": amount,
        "currency": CRYPTOBOT_CURRENCY,
        "description": f"Пополнение баланса для пользователя {user_id}",
        "hidden_message": "Спасибо за использование нашего сервиса!",
        "callback_url": "https://your-server.com/callback",  # Замените на ваш URL для обработки колбэков
        "payload": str(user_id)
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200 and response.json().get("ok"):
        return response.json()["result"]["pay_url"]
    else:
        logger.error(f"Ошибка при создании платежной ссылки: {response.json()}")
        return None

# Функция проверки оплаты
def check_payment_status(invoice_id):
    url = f"{CRYPTOBOT_BASE_URL}getInvoice"
    payload = {
        "token": CRYPTOBOT_API_TOKEN,
        "invoice_id": invoice_id
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200 and response.json().get("ok"):
        invoice = response.json()["result"]
        return invoice["status"] == "paid"  # Возвращает True, если счет оплачен
    else:
        logger.error(f"Ошибка при проверке оплаты: {response.json()}")
        return False

# Функция для обновления баланса
def update_balance(user_id, amount):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    new_balance = balance + amount
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    return new_balance

# Обработчик кнопки "💵 Пополнить баланс"
@bot.message_handler(func=lambda message: message.text == "💵 Пополнить баланс")
def deposit_balance(message):
    user_id = message.from_user.id
    try:
        bot.send_message(user_id, "💵 Введите сумму пополнения в USDT:")
        bot.register_next_step_handler(message, process_deposit_amount)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Произошла ошибка: {e}")

# Обработка ввода суммы и создание платежной ссылки
def process_deposit_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            bot.send_message(user_id, "⚠️ Введите положительное число.")
            return

        # Генерация ссылки для оплаты
        payment_link = create_payment_link(user_id, amount)
        if payment_link:
            bot.send_message(
                user_id,
                f"💵 Для пополнения баланса на **{amount:.2f} USDT**, перейдите по следующей ссылке:\n\n"
                f"{payment_link}UQA3t7ATcPSC-SKs333X4LLry-vJavIziOpVZbMlViRySSGy\n\n"
                f"📊 Баланс будет обновлен автоматически после зачисления.",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(user_id, "⚠️ Не удалось создать платежную ссылку. Попробуйте позже.")
    except ValueError:
        bot.send_message(user_id, "⚠️ Введите корректное число.")

# Опрос статуса платежей
def check_pending_payments():
    while True:
        # Проверяйте неоплаченные счета (храните их в базе данных или списке)
        # Например: [{'invoice_id': '123', 'user_id': 456, 'amount': 10.0}, ...]
        invoices = []  # Здесь должна быть ваша логика для получения счетов
        for invoice in invoices:
            if check_payment_status(invoice["invoice_id"]):
                new_balance = update_balance(invoice["user_id"], invoice["amount"])
                bot.send_message(invoice["user_id"], f"✅ Оплата на сумму {invoice['amount']} USDT успешно зачислена!\n💰 Ваш новый баланс: {new_balance:.2f} Jarli.")
                invoices.remove(invoice)  # Удалите счет после успешной проверки
        time.sleep(60)  # Пауза между проверками

# Запуск опроса в отдельном потоке
import threading

if __name__ == "__main__":
    threading.Thread(target=check_pending_payments, daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling()

