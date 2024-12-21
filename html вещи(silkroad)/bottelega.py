import telebot
import sqlite3
from telebot import types
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import traceback
import csv
import time

# ID администратора
ADMIN_ID = 1007305995  # Замените на ваш Telegram User ID

# Инициализация базы данных
db_path = os.path.abspath('shop.db')
print(f"Путь к базе данных: {db_path}")
if not os.path.exists('shop.db'):
    print("Файл базы данных 'shop.db' не найден. Будет создан новый.")
else:
    print("Файл базы данных 'shop.db' найден.")

# Инициализация бота
TOKEN = "7668678379:AAEKx0YIMFq1QYd2XSvg-Zes76M1Ilo02sU"
bot = telebot.TeleBot(TOKEN)

# Подключение базы данных
db = sqlite3.connect('shop.db', check_same_thread=False)
print(f"Подключение к базе данных открыто: {db}")
cursor = db.cursor()
try:
    # Создание таблицы пользователей
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT
    )""")
    print("Таблица 'users' создана или уже существует.")

    # Создание таблицы корзины
    cursor.execute("""CREATE TABLE IF NOT EXISTS cart (
        user_id INTEGER,
        product_name TEXT,
        product_price TEXT,
        size TEXT,
        color TEXT,
        quantity INTEGER DEFAULT 1
    )""")
    print("Таблица 'cart' создана или уже существует.")
    db.commit()
except sqlite3.Error as e:
    print(f"Ошибка при доступе к базе данных: {e}")

# Словарь для данных пользователя
user_data = {}

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    # Регистрация пользователя
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        db.commit()

    # Главное меню
    main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu.add("🛍️ Магазин", "👤 Профиль", "🛒 Корзина")
    bot.send_message(
        message.chat.id,
        f"👋 <b>Добро пожаловать, {username}!</b>\n\n"
        "Выберите нужное действие из меню ниже или используйте команды:\n"
        "📂 /send_db - Получить базу данных.\n"
        "📄 /send_csv - Получить базу данных в формате CSV.\n"
        "🛒 /get_database - Просмотреть корзину в виде сообщений.",
        parse_mode="HTML",
        reply_markup=main_menu
    )

# Магазин
@bot.message_handler(func=lambda message: message.text == "🛍️ Магазин")
def shop(message):
    bot.send_message(
        message.chat.id,
        "🔗 <b>Отправьте ссылку на товар (например, Taobao):</b>",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(message, parse_product_details)

# Парсинг деталей товара
def parse_product_details(message):
    driver = None  # Объявляем driver на уровне функции
    try:
        site = message.text.strip()
        if not ("taobao" in site or "e.tb.cn" in site):
            bot.send_message(
                message.chat.id,
                "❌ <b>Пожалуйста, отправьте корректную ссылку на товар Taobao.</b>",
                parse_mode="HTML"
            )
            return

        bot.send_message(
            message.chat.id,
            "⏳ <b>Пожалуйста, подождите. Идет обработка товара...</b>",
            parse_mode="HTML"
        )

        # Настройки Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-unsafe-webgl")
        chrome_options.add_argument("--use-gl=swiftshader")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-webgl2")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(site)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1"))
        )

        # Парсинг информации о товаре
        product_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'mainTitle--O1XCl8e2')]").text
        product_price = driver.find_element(By.XPATH, "//span[contains(@class, 'text--Mdqy24Ex')]").text
        currency_symbol = driver.find_element(By.XPATH, "//span[contains(@class, 'unit--i1DKXW20')]").text

        # Преобразование цены
        try:
            price_in_yuan = float(product_price.replace(",", "").strip())
            price_in_rubles = round(price_in_yuan * 14.9, 2)
            price_text = f"{price_in_rubles} ₽"
        except ValueError:
            price_text = "Цена не найдена"

        # Извлечение изображений
        image_elements = driver.find_elements(By.XPATH, "//img[contains(@class, 'mainPic--zxTtQs0P')]")
        if image_elements:
            img_url = image_elements[0].get_attribute('src')
            response = requests.get(img_url)
            if response.status_code == 200:
                with open("temp.jpg", "wb") as f:
                    f.write(response.content)
                with open("temp.jpg", "rb") as f:
                    bot.send_photo(message.chat.id, f)

        # Сохранение данных пользователя
        user_data[message.from_user.id] = {
            "product_name": product_name,
            "product_price": price_text,
            "size": None,
            "color": None
        }

        bot.send_message(
            message.chat.id,
            f" <b>Товар успешно найден!</b>\n\n"
            f"📦 <b>Название:</b> {product_name}\n"
            f"💲 <b>Цена:</b> {price_text}",
            parse_mode="HTML"
        )

        # Отдельное сообщение для ввода размера
        bot.send_message(
            message.chat.id,
            " <b>Введите размер (например, S, M, L):</b>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, choose_size)

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ <b>Ошибка:</b> {e}",
            parse_mode="HTML"
        )
    finally:
        if driver:
            driver.quit()  # Закрываем драйвер, если он был создан
        if os.path.exists("temp.jpg"):
            os.remove("temp.jpg")

# Выбор размера
def choose_size(message):
    user_data[message.from_user.id]["size"] = message.text.strip().upper()
    bot.send_message(
        message.chat.id,
        " <b>Введите цвет (например, Красный, Синий):</b>",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(message, choose_color)

# Выбор цвета
def choose_color(message):
    user_id = message.from_user.id  # Получаем ID пользователя
    if user_id not in user_data:
        bot.send_message(
            message.chat.id,
            "❌ <b>Произошла ошибка. Пожалуйста, начните заново.</b>",
            parse_mode="HTML"
        )
        return

    user_data[user_id]["color"] = message.text.strip().capitalize()  # Сохраняем цвет
    details = user_data[user_id]  # Получаем данные о товаре

    # Создаём кнопку "Добавить в корзину"
    add_to_cart_button = types.InlineKeyboardMarkup()
    add_to_cart_button.add(types.InlineKeyboardButton("🛒 Добавить в корзину", callback_data="add_to_cart"))

    # Отправляем сообщение с полной информацией о товаре
    bot.send_message(
        message.chat.id,
        f"✅ <b>Товар готов к добавлению в корзину!</b>\n\n"
        f"📦 <b>Товар:</b> {details['product_name']}\n"
        f"💲 <b>Цена:</b> {details['product_price']}\n"
        f"📏 <b>Размер:</b> {details['size']}\n"
        f"🎨 <b>Цвет:</b> {details['color']}",
        parse_mode="HTML",
        reply_markup=add_to_cart_button  # Добавляем кнопку
    )



# Обработка кнопки "Добавить в корзину"
@bot.callback_query_handler(func=lambda call: call.data == "add_to_cart")
def add_to_cart(call):
    user_id = call.from_user.id
    details = user_data.get(user_id)

    if details:
        # Добавляем товар в базу данных
        cursor.execute("""
        INSERT INTO cart (user_id, product_name, product_price, size, color, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, details['product_name'], details['product_price'], details['size'], details['color'], 1))
        db.commit()

        # Подтверждаем добавление
        bot.answer_callback_query(call.id, "Товар добавлен в корзину!")
        bot.send_message(call.message.chat.id, "✅ <b>Товар успешно добавлен в корзину!</b>", parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка! Попробуйте снова.")


@bot.message_handler(func=lambda message: message.text == "🛒 Корзина")
def view_cart(message):
    user_id = message.from_user.id

    # Извлекаем товары из корзины
    cursor.execute("SELECT rowid, product_name, product_price, size, color FROM cart WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        bot.send_message(message.chat.id, "🛒 <b>Ваша корзина пуста.</b>", parse_mode="HTML")
        return

    total_price = 0

    for item in cart_items:
        rowid, product_name, product_price, size, color = item
        total_price += float(product_price.replace(" ₽", "").replace(",", "."))  # Суммируем стоимость

        # Создаем кнопки для удаления и оплаты товара
        cart_buttons = types.InlineKeyboardMarkup()
        cart_buttons.add(
            types.InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{rowid}"),
            types.InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{rowid}")
        )

        # Отправляем информацию о каждом товаре
        bot.send_message(
            message.chat.id,
            f"📦 <b>Товар:</b> {product_name}\n"
            f"💲 <b>Цена:</b> {product_price}\n"
            f"📏 <b>Размер:</b> {size}\n"
            f"🎨 <b>Цвет:</b> {color}",
            parse_mode="HTML",
            reply_markup=cart_buttons
        )

    # Отправляем общую сумму
    bot.send_message(
        message.chat.id,
        f"💰 <b>Общая сумма:</b> {total_price:.2f} ₽",
        parse_mode="HTML"
    )

# Обработка кнопки удаления товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_item(call):
    rowid = int(call.data.split("_")[1])

    # Удаляем товар из базы данных
    cursor.execute("DELETE FROM cart WHERE rowid = ?", (rowid,))
    db.commit()

    bot.answer_callback_query(call.id, "❌ Товар удален из корзины.")
    bot.send_message(call.message.chat.id, "❌ <b>Товар успешно удален из корзины.</b>", parse_mode="HTML")

# Обработка кнопки оплаты товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def pay_item(call):
    rowid = int(call.data.split("_")[1])

    # Извлекаем информацию о товаре
    cursor.execute("SELECT product_name, product_price FROM cart WHERE rowid = ?", (rowid,))
    item = cursor.fetchone()

    if item:
        product_name, product_price = item
        payment_url = f"https://www.tbank.ru/cf/1F9OY5hI7md"  # Замените на реальную ссылку оплаты

        # Создаем кнопку для оплаты
        payment_button = types.InlineKeyboardMarkup()
        payment_button.add(types.InlineKeyboardButton("💳 Перейти к оплате", url=payment_url))

        bot.answer_callback_query(call.id, "✅ Операция оплаты начата.")
        bot.send_message(
            call.message.chat.id,
            f"💵 <b>Товар:</b> {product_name}\n"
            f"💰 <b>Сумма:</b> {product_price}\n\n"
            "📨 <b>Нажмите на кнопку ниже, чтобы оплатить.</b>",
            parse_mode="HTML",
            reply_markup=payment_button
        )
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка! Товар не найден.")


while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка в bot.polling: {e}")
        time.sleep(5)  # Задержка перед повторной попыткой
