Саня, [04.02.2025 17:39]
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import sqlite3
from datetime import datetime, timedelta

# Токен вашего бота
TOKEN = '7600799225:AAHtFTGDdxVun58s6Dht5bxsfLHubAq6QLk'

# ID аккаунта администратора (замените на ваш)
ADMIN_CHAT_ID = '422276672'

# Имя файла базы данных
DATABASE_NAME = 'bookings.db'

# Состояния для ConversationHandler
DATE, TIME = range(2)

# Функция для создания таблицы в базе данных
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Функция для добавления бронирования в базу данных
def add_booking(date, time):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bookings (date, time) VALUES (?, ?)', (date, time))
    conn.commit()
    conn.close()

# Функция для получения всех бронирований
def get_all_bookings():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT date, time FROM bookings')
    bookings = cursor.fetchall()
    conn.close()
    return bookings

# Функция для проверки конфликта даты и времени
def is_booking_conflict(date, time):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT date, time FROM bookings WHERE date = ?', (date,))
    bookings = cursor.fetchall()
    conn.close()

    # Преобразуем введённое время в объект datetime
    new_booking_time = datetime.strptime(f'{date} {time}', '%d.%m.%Y %H:%M')

    for booking in bookings:
        existing_booking_time = datetime.strptime(f'{booking[0]} {booking[1]}', '%d.%m.%Y %H:%M')

        # Проверяем интервалы
        if (new_booking_time >= existing_booking_time - timedelta(hours=1)) and \
           (new_booking_time <= existing_booking_time + timedelta(hours=2)):
            return True  # Конфликт есть

    return False  # Конфликта нет

# Функция для команды /start
async def start(update: Update, context: CallbackContext):
    keyboard = [['Забронировать дату']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
    return DATE

# Функция для обработки ввода даты
async def get_date(update: Update, context: CallbackContext):
    await update.message.reply_text('Введите дату для бронирования (в формате ДД.ММ.ГГГГ):', reply_markup=ReplyKeyboardRemove())
    return TIME

# Функция для обработки ввода времени
async def get_time(update: Update, context: CallbackContext):
    date = update.message.text
    try:
        datetime.strptime(date, '%d.%m.%Y')
        context.user_data['date'] = date
        await update.message.reply_text('Введите время для бронирования (в формате ЧЧ:ММ):')
        return TIME
    except ValueError:
        await update.message.reply_text('Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:')
        return DATE

# Функция для завершения бронирования
async def finish_booking(update: Update, context: CallbackContext):
    time = update.message.text
    date = context.user_data['date']
    try:
        datetime.strptime(time, '%H:%M')
        if is_booking_conflict(date, time):
            await update.message.reply_text('Это время конфликтует с существующими бронированиями. Пожалуйста, выберите другое время.')
            return TIME
        else:
            add_booking(date, time)
            bookings = get_all_bookings()
            bookings_text = '\n'.join([f'{b[0]} {b[1]}' for b in bookings])
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f'Новая бронь: {date} {time}\n\nВсе бронирования:\n{bookings_text}'
            )
            await update.message.reply_text(f'Дата "{date} {time}" забронирована.

Саня, [04.02.2025 17:39]
Администратор уведомлён.')
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('Неверный формат времени. Введите время в формате ЧЧ:ММ:')
        return TIME

# Функция для отмены бронирования
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Бронирование отменено.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основная функция для запуска бота
def main():
    # Инициализация базы данных
    init_db()
    
    # Создание приложения бота
    application = Application.builder().token(TOKEN).build()

    # ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_booking)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Регистрируем ConversationHandler
    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()

if name == '__main__':
    main()