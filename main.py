from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
import sqlite3

# Состояния для ConversationHandler
NAME, EMAIL, CLASS, FACULTY = range(4)

# Словарь для соответствия номера факультета и названия
FACULTY_DICT = {
    '1': 'IT',
    '2': 'Science',
    '3': 'Sport',
    '4': 'Languages'
}

# Словарь для соответствия номера факультета и ссылки
FACULTY_LINKS = {
    '1': 'ССЫЛКА НА ФАКУЛЬТЕТ IT',
    '2': 'ССЫЛКА НА ФАКУЛЬТЕТ SCINCE',
    '3': 'ССЫЛКА НА ФАКУЛЬТЕТ SPORT',
    '4': 'ССЫЛКА НА ФАКУЛЬТЕТ LANGUAGES'
}

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("1 - IT", callback_data='1')],
        [InlineKeyboardButton("2 - Science", callback_data='2')],
        [InlineKeyboardButton("3 - Sport", callback_data='3')],
        [InlineKeyboardButton("4 - Languages", callback_data='4')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите факультет:", reply_markup=reply_markup)
    return FACULTY

# Функция для обработки нажатия на кнопку
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['faculty'] = FACULTY_DICT[query.data]
    query.message.reply_text("Введите ваше имя и фамилию:")
    return NAME

# Функция для обработки ввода имени и фамилии
def get_name(update: Update, context: CallbackContext) -> None:
    name = update.message.text
    context.user_data['name'] = name
    update.message.reply_text("Введите ваш email:")
    return EMAIL

# Функция для обработки ввода email и класса
def get_email(update: Update, context: CallbackContext) -> None:
    email = update.message.text
    context.user_data['email'] = email
    update.message.reply_text("Введите ваш класс:")
    return CLASS

# Функция для обработки ввода класса и завершения регистрации
def get_class(update: Update, context: CallbackContext) -> None:
    class_ = update.message.text
    context.user_data['class'] = class_
    user_id = update.message.from_user.id
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    if user:
        update.message.reply_text("Вы уже зарегистрированы.")
    else:
        c.execute("INSERT INTO users (user_id, name, email, class, faculty) VALUES (?, ?, ?, ?, ?)", (user_id, context.user_data['name'], context.user_data['email'], context.user_data['class'], context.user_data['faculty']))
        conn.commit()
        conn.close()
        update.message.reply_text("Регистрация успешно завершена!")
        update.message.reply_text(FACULTY_LINKS[context.user_data['faculty']])  # Отправляем ссылку
    return ConversationHandler.END

# Функция для обработки команды /list
def list_users(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name, class FROM users WHERE faculty = ?", (context.user_data['faculty'],))
    users = c.fetchall()
    conn.close()

    if users:
        user_list = "\n".join([f"{name} - класс {class_}" for name, class_ in users])
        update.message.reply_text(f"Пользователи на факультете {context.user_data['faculty']}:\n{user_list}")
    else:
        update.message.reply_text(f"На факультете {context.user_data['faculty']} пока нет зарегистрированных пользователей.")

def main() -> None:
    updater = Updater("6116656907:AAHY_pds7QgOTY-s0UqErlb_Vnc7erVmJng")
    dispatcher = updater.dispatcher

    # Создание таблицы пользователей в базе данных SQLite
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
             (user_id INTEGER PRIMARY KEY, name TEXT, email TEXT, class INTEGER, faculty TEXT)''')
    c.execute('''ALTER TABLE users ADD COLUMN name TEXT''')
    conn.commit()
    conn.close()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FACULTY: [CallbackQueryHandler(button)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
            CLASS: [MessageHandler(Filters.text & ~Filters.command, get_class)]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('list', list_users, pass_user_data=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
