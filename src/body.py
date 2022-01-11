import telebot as tb
from telebot import types
import config
import time
import sqlite3


def main():
    # Подключаемся к боту
    bot = tb.TeleBot(config.TOKEN)
    # Подключаем базу
    conn = sqlite3.connect('db/database', check_same_thread=False)
    # Создаем курсор для работы с таблицами
    cursor = conn.cursor()
    stop_text = ['нет', 'выход', 'выйти', 'меню', '/menu', '/region', '/start', 'сдать', 'снять']

    # Чекаем на наличие @юзернейма
    def check_username(message):
        if message.from_user.username is None:
            t = 'Я заметил, что у тебя нету (@ username)! Пожалуйста, добавь его в настройках своего аккаунта. ' \
                'Без этого пользователи бота не смогут с тобой взаимодействовать :('
            bot.send_message(message.chat.id, t)
            return 0
        else:
            return message

    # Главное меню
    def main_menu(message, t):
        keyboard_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_menu = ['Сдать', 'Меню', 'Снять', 'Посмотреть мои обьявления']
        keyboard_main.add(button_menu[0], button_menu[1], button_menu[2])
        keyboard_main.add(button_menu[3])
        bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=keyboard_main)

        markup = types.InlineKeyboardMarkup()
        key1 = types.InlineKeyboardButton('Сдать товар в аренду', callback_data='1')
        key2 = types.InlineKeyboardButton('Арендовать чей-то товар', callback_data='2')
        key3 = types.InlineKeyboardButton('Посмотреть все мои объявления',
                                          callback_data='3')
        key4 = types.InlineKeyboardButton('Посмотреть все объявления о сдаче',
                                          callback_data='11')
        key5 = types.InlineKeyboardButton(
            'Посмотреть все объявления о поиске', callback_data='77')
        # key6 = types.InlineKeyboardButton('Создать объявление о поиске', callback_data='search')

        markup.row(key1)
        markup.row(key2)
        markup.row(key3)
        markup.row(key4)
        markup.row(key5)
        # markup.row(key6)

        msg = bot.send_message(message.chat.id,
                               'Выбери, что мы будем делать сегодня:', parse_mode='html', reply_markup=markup)
        return msg

    def how_many_obj(category, u_id):
        cursor.execute(
            'SELECT COUNT(category) FROM obj WHERE category = ? '
            'AND region = (SELECT user_region FROM user WHERE user_id = ?)',
            (category, u_id,))
        how_many = ((str(cursor.fetchone())).split(',')[0]).strip('(')
        print(how_many)
        if how_many == '0':
            return ' '
        else:
            how_many = ' (' + how_many + ')'
            return how_many

    # ------------------------------Функция для регистрации пользователя------------------------------------------------
    def db_table_val(user_id: int, user_name: str, user_region: str, user_registration: int, chat_id: int):
        cursor.execute('INSERT INTO user (user_id, user_name, user_region, user_registration, '
                       'chat_id) VALUES (?, ?, ?, ?, ?)',
                       (user_id, user_name, user_region, user_registration, chat_id))
        conn.commit()

    # --------------------------------------ОБРАБОТЧИК КОМАНДЫ СТАРТ----------------------------------------------------
    @bot.message_handler(commands=['start'])
    def welcome(message):
        # ------------------------ПРОВЕРКА НА НАЛИЧИЕ В БД ПОЛЬЗОВАТЕЛЯ------------------------
        if check_username(message) == 0:
            pass
        else:
            u_id = message.from_user.id
            info = cursor.execute('SELECT * FROM user WHERE user_id=?', (u_id,))
            if info.fetchone() is None:
                msg = bot.send_message(message.chat.id,
                                       'Добро пожаловать!\n' +
                                       'Укажи, пожалуйста, свой город.')
                if msg.text:
                    bot.register_next_step_handler(msg, check_city)
            else:
                u_name = message.from_user.first_name
                t = 'Чем займемся сегодня, {}?'.format(u_name)
                main_menu(message, t)

    # ----------------------APPLY() - О СОГЛАСИИ УВЕДОМЛЕНИЙ--------------------------------
    def apply(message):
        markup = types.InlineKeyboardMarkup()
        key1 = types.InlineKeyboardButton(
            'Только в моём районе.',
            callback_data='Yes')
        key2 = types.InlineKeyboardButton('Выбрать несколько районов.',
                                          callback_data='Yes+')
        key3 = types.InlineKeyboardButton('Я не хочу получать уведомления',
                                          callback_data='No')

        markup.row(key1)
        markup.row(key2)
        markup.row(key3)
        key = bot.send_message(message.chat.id,
                               'География понятна! Каждый день я помогаю соседям найти необходимые вещи. ' +
                               'Если ты готов сдавать что-то в аренду, я могу сообщить,' +
                               'когда твоим соседям что-нибудь понадобится. ' +
                               'Можно?) '.format(message.from_user, bot.get_me()), parse_mode='html',
                               reply_markup=markup)
        return key

    # ------------------ПОЛНАЯ РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ В БД ПОСЛЕ ТОГО КАК ОН ВВЕДЕТ РЕГИОН------------------------
    def region(message):
        u_id = message.from_user.id
        chat_id = message.chat.id
        u_name = "@" + message.from_user.username
        u_region = message.text
        get_reg = ["Академический", "Алексеевский", "Алтуфьевский", "Арбат", "Аэропорт",
                   "Бабушкинский", "Басманный", "Беговой", "Бескудниковский", "Бибирево",
                   "Бирюлёво восточное", "Бирюлёво западное", "Богородское", "Братеево",
                   "Бутово северное", "Бутово южное", "Бутырский", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Гагаринский",
                   "Головинский", "Гольяново", "Ганиловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Замоскворечье",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Левобережный", "Лефортово", "Лианозово", "Ломоносовский",
                   "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково северное", "Медведково южное", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Перово", "Печатники",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Таганский", "Тверской", "Текстильщики", "Тёплый стан",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Хамовники", "Ховрино", "Хорошёво-мневники",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Щукино", "Южнопортовый",
                   "Якиманка", "Ярославский", "Ясенево"]

        for x in get_reg:
            if u_region.lower() == x.lower():
                db_table_val(user_id=u_id, user_name=u_name, user_region=x, user_registration=3, chat_id=chat_id)
                apply(message)
                break
        else:
            t = 'Не нашёл твой регион, попробуй еще раз. Вот список доступных районов:\n\n{}'.format('\n'.join(get_reg))
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, region)

    def check_city(message):
        city = ['Москва', 'москва', 'масква', 'Масква', 'Мск', 'Москоу', 'Moscow', 'moscow', 'msc']
        if message.text in city:
            msg = bot.send_message(message.chat.id,
                                   'Укажи, пожалуйста, свой район, чтобы я мог подключить' +
                                   'тебя к дружной сети соседей :)')
            if msg.text:
                bot.register_next_step_handler(msg, region)
        else:
            with open("city.txt", "a") as file:
                file.write('-' + message.text + '\n')
                file.close()
            bot.send_message(message.chat.id, 'К сожалению, Соседи пока захватывают только Москву.\n'
                                              'Я запомнил твой город, чтобы мы скорее могли встретиться!\n'
                                              '\nА пока следи за нашими обновлениями в Instagram:\n'
                                              'https://instagram.com/sosedi.sharing')

    # ------------------------ОБРАБОТЧИК КОМАНДЫ МЕНЮ--------------------------------------------
    @bot.message_handler(commands=['menu'])
    def get_menu(message):
        if check_username(message) == 0:
            pass
        else:
            t = 'Возвращаемся к меню...'
            main_menu(message, t)

    # ------------------------ОБРАБОТЧИК КОМАНДЫ СМЕНИТЬ РЕГИОН----------------------------------
    @bot.message_handler(commands=['region'])
    def change_region(message):
        if check_username(message) == 0:
            pass
        else:
            t = 'Хочешь поменять свой район? Введи название района, например : Северный'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, change_user_region)

    def change_user_region(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_region = message.text
        u_id = message.from_user.id
        get_reg = ["Академический", "Алексеевский", "Алтуфьевский", "Арбат", "Аэропорт",
                   "Бабушкинский", "Басманный", "Беговой", "Бескудниковский", "Бибирево",
                   "Бирюлёво восточное", "Бирюлёво западное", "Богородское", "Братеево",
                   "Бутово северное", "Бутово южное", "Бутырский", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Гагаринский",
                   "Головинский", "Гольяново", "Ганиловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Замоскворечье",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Левобережный", "Лефортово", "Лианозово", "Ломоносовский",
                   "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково северное", "Медведково южное", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Перово", "Печатники",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Таганский", "Тверской", "Текстильщики", "Тёплый стан",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Хамовники", "Ховрино", "Хорошёво-мневники",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Щукино", "Южнопортовый",
                   "Якиманка", "Ярославский", "Ясенево"]
        for x in get_reg:
            if u_region.lower() == x.lower():
                cursor.execute('UPDATE user SET user_region = ? WHERE user_id = ?', (x, u_id,))
                conn.commit()
                cursor.execute('UPDATE obj SET region = ? WHERE u_id = ?', (x, u_id,))
                conn.commit()
                cursor.execute('UPDATE search_obj SET region = ? WHERE u_id = ?', (x, u_id,))
                conn.commit()
                t = 'Я поменял твой район и отредактировал его в твоих обьявлениях! Теперь твой район - {}'.format(x)
                main_menu(message, t)
                break
        else:
            t = 'Не нашёл такой район.'
            main_menu(message, t)

    # -------------------------ОБРАБОТЧИК ВСЕХ КОЛЛ ОТВЕТОВ ОТ ПОЛЬЗОВАТЕЛЯ-----------------------
    @bot.callback_query_handler(func=lambda call: True)
    def apply_get(call):
        message = call.message
        if call.data == 'No':
            t = 'Как скажешь! Никаких уведомлений :)'
            app_num = 3
            u_id = call.from_user.id
            cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
                           (app_num, u_id,))
            conn.commit()
            cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            conn.commit()
            bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id,
                                          reply_markup=None)  # удаляем кнопки у последнего сообщения
            main_menu(message, t)
        if call.data == 'Yes':
            app_num = 2
            u_id = call.from_user.id
            cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
                           (app_num, u_id,))
            conn.commit()
            cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            conn.commit()
            bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id,
                                          reply_markup=None)  # удаляем кнопки у последнего сообщения
            t = 'Супер! Договорились, я буду присылать тебе уведомления только о поиске в твоем районе.'
            main_menu(message, t)
        if call.data == 'Yes+':
            app_num = 1
            u_id = call.from_user.id
            cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
                           (app_num, u_id,))
            conn.commit()
            bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id,
                                          reply_markup=None)  # удаляем кнопки у последнего сообщения
            t = 'Отлично! Напиши районы, о поиске вещей в которых ты бы хотел получать уведомления.\n' \
                'Например: Арбат, Царицыно, Внуково'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_message_init)

        # --------MENU--------
        if call.data == 'menu':
            t = 'Главное меню'
            main_menu(message, t)

        # ---------СДАЕМ---------
        if call.data == '1':
            t = 'Здорово, что ты готов сдать что-то в аренду! Я помогу тебе составить объявление. ' \
                'Давай начнем с категории товара, который ты бы хотел сдать в аренду. Выбери подходящее:'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Фото и видео',
                                              callback_data='1-1')
            key2 = types.InlineKeyboardButton('Техника для дома',
                                              callback_data='1-2')
            key3 = types.InlineKeyboardButton('Игры и консоли',
                                              callback_data='1-3')
            key4 = types.InlineKeyboardButton(
                'Туризм и путешествия',
                callback_data='1-4')
            key5 = types.InlineKeyboardButton('Декор и мебель',
                                              callback_data='1-5')
            key6 = types.InlineKeyboardButton('Детские товары',
                                              callback_data='1-6')
            key7 = types.InlineKeyboardButton('Для мероприятий',
                                              callback_data='1-7')
            key8 = types.InlineKeyboardButton('Инструменты',
                                              callback_data='1-8')
            key9 = types.InlineKeyboardButton('Товары для спорта',
                                              callback_data='1-9')
            key10 = types.InlineKeyboardButton('Музыка и хобби',
                                               callback_data='1-10')
            key11 = types.InlineKeyboardButton('Прочее', callback_data='1-11')
            key12 = types.InlineKeyboardButton('Выйти в МЕНЮ', callback_data='menu')
            markup.row(key12)
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key4)
            markup.row(key5)
            markup.row(key6)
            markup.row(key7)
            markup.row(key8)
            markup.row(key9)
            markup.row(key10)
            markup.row(key11)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)

        # --------АРЕНДУЕМ-------
        if call.data == '2':
            u_id = call.from_user.id
            t = 'Понял тебя, арендуем! Уже вспоминанию все объявления твоих соседей! ' \
                'Выбери категорию, в которой находится нужный тебе предмет.'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Фото и видео {}'.format(how_many_obj('Фото и видео', u_id)),
                                              callback_data='2-1')
            key2 = types.InlineKeyboardButton('Техника для дома {}'.format(how_many_obj('Техника для дома', u_id)),
                                              callback_data='2-2')
            key3 = types.InlineKeyboardButton('Игры и консоли {}'.format(how_many_obj('Игры и консоли', u_id)),
                                              callback_data='2-3')
            key4 = types.InlineKeyboardButton(
                'Туризм и путешествия {}'.format(how_many_obj('Туризм и путешествия', u_id)),
                callback_data='2-4')
            key5 = types.InlineKeyboardButton('Декор и мебель {}'.format(how_many_obj('Декор и мебель', u_id)),
                                              callback_data='2-5')
            key6 = types.InlineKeyboardButton('Детские товары {}'.format(how_many_obj('Детские товары', u_id)),
                                              callback_data='2-6')
            key7 = types.InlineKeyboardButton('Для мероприятий {}'.format(how_many_obj('Для мероприятий', u_id)),
                                              callback_data='2-7')
            key8 = types.InlineKeyboardButton('Инструменты {}'.format(how_many_obj('Инструменты', u_id)),
                                              callback_data='2-8')
            key9 = types.InlineKeyboardButton('Товары для спорта {}'.format(how_many_obj('Товары для спорта', u_id)),
                                              callback_data='2-9')
            key10 = types.InlineKeyboardButton('Музыка и хобби {}'.format(how_many_obj('Музыка и хобби', u_id)),
                                               callback_data='2-10')
            key11 = types.InlineKeyboardButton('Прочее {}'.format(how_many_obj('Прочее', u_id)), callback_data='2-11')
            key12 = types.InlineKeyboardButton('Выйти в МЕНЮ', callback_data='menu')
            key13 = types.InlineKeyboardButton('Создать объявление о поиске', callback_data='search')
            markup.row(key12)
            markup.row(key13)
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key4)
            markup.row(key5)
            markup.row(key6)
            markup.row(key7)
            markup.row(key8)
            markup.row(key9)
            markup.row(key10)
            markup.row(key11)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)

        # --------АРЕНДУЕМ ПОИСК-----------------------
        if call.data == '2-1':
            category = 'Фото и видео'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-2':
            category = 'Техника для дома'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-3':
            category = 'Игры и консоли'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-4':
            category = 'Туризм и путешествия'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-5':
            category = 'Декор и мебель'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-6':
            category = 'Детские товары'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-7':
            category = 'Для мероприятий'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-8':
            category = 'Инструменты'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-9':
            category = 'Товары для спорта'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-10':
            category = 'Музыка и хобби'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-11':
            category = 'Прочее'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)

        # ---------------------------------------------------------------------------------------------------
        if call.data == '2-1+':
            t = 'Круто! Тогда смело пиши владельцу :) Он тебя уже ждет!'
            main_menu(message, t)
        if call.data == '2-1-':
            t = 'Не подходит? Тогда давай я спрошу всех соседей? У кого-то 100% есть!'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
            key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
            markup.row(key1)
            markup.row(key2)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)
        if call.data == '2-1---':
            t = 'Чтобы я точно передал всем твою просьбу - давай создадим объявление. \n' \
                'Напиши еще раз название, что ты ищешь: '
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)
        if call.data == '2-1-++':
            t = 'Тогда возвращаю тебе меню...'
            main_menu(message, t)
        if call.data == '2-1-0':
            t = 'Выбери, что хочешь изменить ->'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Название', callback_data='2-1-0-1')
            key2 = types.InlineKeyboardButton('Описание', callback_data='2-1-0-2')
            markup.row(key1)
            markup.row(key2)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)
        if call.data == '2-1-0-1':
            t = 'Введи новое название'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)
        if call.data == '2-1-0-2':
            t = 'Введи новое описание'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)

        if call.data == '2-1-1':
            send_push(call)
            t = 'Соседская поисковая машина запущена! Мне понадобится немного времени, ' \
                'но я сообщу сразу, как только найду подходящие для тебя варианты)'
            main_menu(message, t)

        # --------ПОСМОТРЕТЬ ВСЕ МОИ ОБЬЯВЛЕНИЯ---------
        if call.data == '3':
            t = 'Какие обьявления смотрим?'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Что я сдаю?', callback_data='3-1-1')
            key2 = types.InlineKeyboardButton('Что я ищу в аренду?', callback_data='3-1-2')
            markup.row(key1)
            markup.row(key2)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)
        if call.data == '3-1-1':
            u_id = call.from_user.id
            cursor.execute('DELETE FROM obj WHERE u_id = ? AND photo IS NULL OR money_cat1 IS NULL OR cat_1 IS NULL',
                           (u_id,))
            conn.commit()
            cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_comment IS NULL', (u_id,))
            conn.commit()
            cursor.execute("SELECT * FROM 'obj' WHERE u_id = ?",
                           (u_id,))
            result = cursor.fetchall()
            if result:
                bot.send_message(message.chat.id,
                                 "Вот все твои действующие объявления: ",
                                 parse_mode='html')
                for x in result:
                    bot.send_photo(message.chat.id, x[6])
                    markup = types.InlineKeyboardMarkup()
                    key1 = types.InlineKeyboardButton('Удалить', callback_data='delete1')
                    markup.row(key1)
                    bot.send_message(message.chat.id,
                                     "Категория:{}\n\nНазвание:{}\n\nЦена:{}р\n\nОписание:{}"
                                     "\n\nВладелец:{}".format(x[7], x[2], x[3], x[4], x[5]),
                                     parse_mode='html', reply_markup=markup)
            else:
                t = 'Что-то не припомню, чтобы мы с тобой создавали вместе объявление :( Хочешь попробовать?'
                main_menu(message, t)

        if call.data == '3-1-2':
            u_id = call.from_user.id
            cursor.execute('DELETE FROM obj WHERE u_id = ? AND photo IS NULL OR money_cat1 IS NULL OR cat_1 IS NULL',
                           (u_id,))
            conn.commit()
            cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_comment IS NULL', (u_id,))
            conn.commit()
            cursor.execute("SELECT * FROM 'search_obj' WHERE u_id = ?",
                           (u_id,))
            result = cursor.fetchall()
            if result:
                bot.send_message(message.chat.id,
                                 "Вот все активные запросы на поиск, которые ты создал: ",
                                 parse_mode='html')
                for x in result:
                    markup = types.InlineKeyboardMarkup()
                    key1 = types.InlineKeyboardButton('Удалить', callback_data='delete2')
                    markup.row(key1)
                    bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что :)\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     .format(x[4], x[2], x[3]),
                                     reply_markup=markup)
            else:
                t = 'Что-то не припомню, чтобы мы с тобой создавали запрос. Хочешь попробовать?'
                main_menu(message, t)

        # --===---ПОСМОТРЕТЬ ВСЕ ОБЬЯВЛЕНИЯ О СДАЧЕ В КАТЕГОРИИ-----------
        if call.data == '11':
            u_id = call.from_user.id
            t = 'Выбери категорию:'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Фото и видео {}'.format(how_many_obj('Фото и видео', u_id)),
                                              callback_data='11-1')
            key2 = types.InlineKeyboardButton('Техника для дома {}'.format(how_many_obj('Техника для дома', u_id)),
                                              callback_data='11-2')
            key3 = types.InlineKeyboardButton('Игры и консоли {}'.format(how_many_obj('Игры и консоли', u_id)),
                                              callback_data='11-3')
            key4 = types.InlineKeyboardButton(
                'Туризм и путешествия {}'.format(how_many_obj('Туризм и путешествия', u_id)),
                callback_data='11-4')
            key5 = types.InlineKeyboardButton('Декор и мебель {}'.format(how_many_obj('Декор и мебель', u_id)),
                                              callback_data='11-5')
            key6 = types.InlineKeyboardButton('Детские товары {}'.format(how_many_obj('Детские товары', u_id)),
                                              callback_data='11-6')
            key7 = types.InlineKeyboardButton('Для мероприятий {}'.format(how_many_obj('Для мероприятий', u_id)),
                                              callback_data='11-7')
            key8 = types.InlineKeyboardButton('Инструменты {}'.format(how_many_obj('Инструменты', u_id)),
                                              callback_data='11-8')
            key9 = types.InlineKeyboardButton('Товары для спорта {}'.format(how_many_obj('Товары для спорта', u_id)),
                                              callback_data='11-9')
            key10 = types.InlineKeyboardButton('Музыка и хобби {}'.format(how_many_obj('Музыка и хобби', u_id)),
                                               callback_data='11-10')
            key11 = types.InlineKeyboardButton('Прочее {}'.format(how_many_obj('Прочее', u_id)),
                                               callback_data='11-11')
            key12 = types.InlineKeyboardButton('Выйти в МЕНЮ', callback_data='menu')
            markup.row(key12)
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key4)
            markup.row(key5)
            markup.row(key6)
            markup.row(key7)
            markup.row(key8)
            markup.row(key9)
            markup.row(key10)
            markup.row(key11)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)
        if call.data == '11-1':
            category = 'Фото и видео'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-2':
            category = 'Техника для дома'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-3':
            category = 'Игры и консоли'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-4':
            category = 'Туризм и путешествия'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-5':
            category = 'Декор и мебель'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-6':
            category = 'Детские товары'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-7':
            category = 'Для мероприятий'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-8':
            category = 'Инструменты'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-9':
            category = 'Товары для спорта'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-10':
            category = 'Музыка и хобби'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)
        if call.data == '11-11':
            category = 'Прочее'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == '0':
                t = 'В категории({}) нету объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'Ищем в категории {}, все верно?'.format(category)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, look_obj, category)

        # ----------ПОСМОТРЕТЬ ВСЕ ОБЪЯВЛЕНИЯ О ПОИСКЕ В АРЕНДУ------------
        if call.data == '77':
            t = 'Вот что сейчас ищут...'
            u_id = call.from_user.id
            cursor.execute("SELECT user_region FROM 'user' WHERE user_id = ?", (u_id,))
            user_region = cursor.fetchone()
            cursor.execute("SELECT * FROM 'search_obj' WHERE obj_comment IS NOT NULL AND region = ?",
                           (user_region[0],))
            result = cursor.fetchall()
            if result:
                bot.send_message(message.chat.id, t)
                for x in result:
                    bot.send_message(message.chat.id,
                                     "{} - срочно ищет кое-что :)\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     .format(x[4], x[2], x[3]))
            else:
                t = 'В твоём районе нет активных запросов на поиск.'
                main_menu(message, t)

        # -----СДАТЬ В КАТЕГОРИИ -----
        if call.data == '1-1':
            t = 'Супер! А что именно из категории (Фото и видео) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Фото и видео'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-2':
            t = 'Супер! А что именно из категории (Техника для дома) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Техника для дома'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-3':
            t = 'Супер! А что именно из категории (Игры и консоли) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Игры и консоли'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-4':
            t = 'Супер! А что именно из категории (Туризм и путешествия) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Туризм и путешествия'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-5':
            t = 'Супер! А что именно из категории (Декор и мебель) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Декор и мебель'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-6':
            t = 'Супер! А что именно из категории (Детские товары) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Детские товары'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-7':
            t = 'Супер! А что именно из категории (Для мероприятий) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Для мероприятий'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-8':
            t = 'Супер! А что именно из категории (Инструменты) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Инструменты'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-9':
            t = 'Супер! А что именно из категории (Товары для спорта) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Товары для спорта'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-10':
            t = 'Супер! А что именно из категории (Музыка и хобби) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Музыка и хобби'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-11':
            t = 'Супер! А что именно из категории (Прочее) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно :)'
            z = 'Прочее'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        # -----ПОДТВЕРДИТЬ ТОЛЬКО ЧТО СОЗДАННОЕ ОБЬЯВЛЕНИЕ(КАТ_1)------
        if call.data == '01':
            t = 'Супер! Объявление добавлено.'
            main_menu(message, t)

        # ----РЕДАКТИРОВАТЬ ТОЛЬКО ЧТО СОЗДАННОЕ ОБЬЯВЛЕНИЕ(КАТ_1)---------------
        if call.data == '01-1':
            t = 'Выбери, что ты хочешь изменить ->'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Название', callback_data='01-1-1')
            key2 = types.InlineKeyboardButton('Цена', callback_data='01-1-2')
            key3 = types.InlineKeyboardButton('Описание', callback_data='01-1-3')
            key5 = types.InlineKeyboardButton('Фото', callback_data='01-1-5')
            key4 = types.InlineKeyboardButton('Удалить', callback_data='01-1-4')
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key5)
            markup.row(key4)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)
        if call.data == '01-1-4':
            u_id = call.from_user.id
            cursor.execute('DELETE FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (u_id,))
            conn.commit()
            t = 'Я удалил твоё последнее объявление.\n'
            main_menu(message, t)
        if call.data == '01-1-1':
            t = 'Введи НОВОЕ название объявления'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_name_obj)
        if call.data == '01-1-2':
            t = 'Введи НОВУЮ цену объявления'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_money_obj)
        if call.data == '01-1-3':
            t = 'Введи НОВОЕ описание объявления'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_text_obj)
        if call.data == '01-1-5':
            t = 'Отправь НОВУЮ фотографию для объявления'
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_photo_obj)

        # --------УДАЛИТЬ ОБЬЯВЛЕНИЕ----------------------------------------
        if call.data == 'delete1':
            t = 'Введи название своего обьявления, которое ты хочешь удалить.'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, delete_obj)

        if call.data == 'delete2':
            t = 'Введи название своего обьявления, которое ты хочешь удалить.'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, delete_search_obj)

        # --------сОЗДАТЬ ОБЪЯВЛЕНИЕ О ПОИСКЕ В АРЕНДУ-------------
        if call.data == 'search':
            t = 'Хочешь создать объявление о поиске в аренду?'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
            key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
            markup.row(key1)
            markup.row(key2)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t, reply_markup=markup)

    # -------------------------ФУНКЦИЯ ПОЛУЧЕНИЯ УВЕДОМЛЕНИЙ В НЕСКОЛЬКИХ РАЙОНАХ-------------------------------
    def search_message_init(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_reg = message.text
        u_region = [str(x) for x in u_reg.split(', ')]
        u_id = message.from_user.id
        get_reg = ["Академический", "Алексеевский", "Алтуфьевский", "Арбат", "Аэропорт",
                   "Бабушкинский", "Басманный", "Беговой", "Бескудниковский", "Бибирево",
                   "Бирюлёво восточное", "Бирюлёво западное", "Богородское", "Братеево",
                   "Бутово северное", "Бутово южное", "Бутырский", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Гагаринский",
                   "Головинский", "Гольяново", "Ганиловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Замоскворечье",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Левобережный", "Лефортово", "Лианозово", "Ломоносовский",
                   "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково северное", "Медведково южное", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Перово", "Печатники",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Таганский", "Тверской", "Текстильщики", "Тёплый стан",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Хамовники", "Ховрино", "Хорошёво-мневники",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Щукино", "Южнопортовый",
                   "Якиманка", "Ярославский", "Ясенево"]
        cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_id,))
        result = cursor.fetchone()
        u_region.append(result[0])
        if set(u_region).issubset(get_reg) == 1:
            result = ", ".join(list(set(get_reg).intersection(set(u_region))))
            cursor.execute('UPDATE user SET search_message = ? WHERE user_id = ?', (result, u_id,))
            conn.commit()
            t = 'Понял тебя. Теперь буду сообщать тебе о поиске в этих районах: {}'.format(result)
            main_menu(message, t)
        else:
            t = 'Не нашёл все районы, пожалуйста, попробуй еще раз.\n' \
                'Ввод должен быть таким: Арбат, Царицыно, Внуково\n\n' \
                'Вот список доступных районов:\n\n{}' \
                .format('\n'.join(get_reg))
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_message_init)

    # -----------------ФУНКЦИЯ ДЛЯ ПРОСМОТРА ВСЕХ ОБ. ПО КАТЕГОРИЯМ И РЕГИОНУ ПОЛЬЗОВАТЕЛЯ----------------------
    def look_obj(message, category):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_id = message.from_user.id
        cursor.execute("SELECT user_region FROM user WHERE user_id = ?", (u_id,))
        u_region = cursor.fetchone()
        cat = '{}'.format(category)
        cursor.execute("SELECT * FROM 'obj' WHERE "
                       "cat_1 IS NOT NULL AND name_cat1_obj IS NOT NULL AND photo IS NOT NULL "
                       "AND category = ? AND region = ?", (cat, u_region[0],))
        result = cursor.fetchall()
        if result:
            bot.send_message(message.chat.id,
                             "Вот все действующие объявления: ",
                             parse_mode='html')
            for x in result:
                bot.send_photo(message.chat.id, x[6])
                bot.send_message(message.chat.id,
                                 "Категория: {}\n\nНазвание: {}\n\nЦена: {}р\n\nОписание :{}"
                                 "\n\nВладелец:{}".format(x[7], x[2], x[3], x[4], x[5]),
                                 parse_mode='html')
        else:
            t = 'Похоже, еще никто не создал объявление :( Хочешь попробовать?'
            main_menu(message, t)

    # ------------------------------ФУНКЦИИ ДЛЯ УДАЛЕНИЯ ОБЬЯВЛЕНИЙ-------------------------------------
    def delete_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_id = message.from_user.id
        u_text = message.text
        cursor.execute('SELECT name_cat1_obj FROM obj WHERE u_id = ?', (u_id,))
        result = cursor.fetchall()
        for x in result:
            a = x[0]
            if u_text.lower() == a.lower():
                cursor.execute('DELETE FROM obj WHERE u_id = ? AND name_cat1_obj = ?', (u_id, a,))
                conn.commit()
                t = 'Я удалил обьявление ({})'.format(a)
                bot.send_message(message.chat.id, t)
                break
        else:
            t = 'Я не нашел в списке твоих обьявлений такое название.'
            bot.send_message(message.chat.id, t)

    def delete_search_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_id = message.from_user.id
        u_text = message.text
        cursor.execute('SELECT obj_name FROM search_obj WHERE u_id = ?', (u_id,))
        result = cursor.fetchall()
        for x in result:
            a = x[0]
            if u_text.lower() == a.lower():
                cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_name = ?', (u_id, a,))
                conn.commit()
                t = 'Я удалил обьявление {}'.format(a)
                bot.send_message(message.chat.id, t)
                break
        else:
            t = 'Я не нашел в списке твоих обьявлений такое название.'
            bot.send_message(message.chat.id, t)

    # --------------------------------------ФУНКЦИЯ ДЛЯ УВЕДОМЛЕНИЯ---------------------------------------------
    def send_push(message):
        u1_id = message.from_user.id
        cursor.execute('SELECT user_region FROM user WHERE user_id = ?',
                       (u1_id,))
        u1_region = cursor.fetchall()
        cursor.execute('SELECT chat_id FROM user WHERE user_registration = ? OR user_registration = ?',
                       (1, 2))
        u2_id = cursor.fetchall()
        if u2_id:
            for x in u2_id:
                cursor.execute('SELECT search_message FROM user WHERE user_id = ?',
                               (x[0],))
                region_lst = cursor.fetchall()
                if u1_region[0][0] in region_lst[0][0]:
                    cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj '
                                   'WHERE u_id = ?)', (u1_id,))
                    result = cursor.fetchone()
                    bot.send_message(x[0],
                                     "Всем привет!\n{} - срочно ищет кое-что :)\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     .format(result[4], result[2], result[3]))
        else:
            return 0

    # ----------------------------------------ФУНКЦИИ ВЕТКИ СЬЕМ------------------------------------------------

    def search_cat1(message, category):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        cat = '{}'.format(category)
        cursor.execute("SELECT user_region FROM user WHERE user_id = ?", (u_id,))
        u_region = cursor.fetchone()
        cursor.execute("SELECT * FROM 'obj' WHERE "
                       "cat_1 IS NOT NULL AND name_cat1_obj IS NOT NULL AND photo IS NOT NULL "
                       "AND category = ? AND region = ?", (cat, u_region[0],))
        result = cursor.fetchall()
        if len(u_text) > 2 and u_text.isdigit() == 0:
            r = 0
            for x in result:
                a = x[2]
                if u_text.lower() in a.lower():
                    bot.send_message(message.chat.id, 'Смотри, что я нашел!')
                    bot.send_photo(message.chat.id, x[6])
                    bot.send_message(message.chat.id, 'Название: {}\n\nЦена: {}р\n\nОписание: {}\n\nВладелец: {}'
                                     .format(x[2], x[3], x[4], x[5]))
                    r = r + 1
            if r != 0:
                t = 'Нашел ли ты нужное или все не то?'
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Подходит!', callback_data='2-1+')
                key2 = types.InlineKeyboardButton('Я не нашёл, что искал', callback_data='2-1-')
                markup.row(key1)
                markup.row(key2)
                bot.send_message(message.chat.id, t, reply_markup=markup)
            if r == 0:
                t = 'Таких объявлений нет, давай создадим запрос?'
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                bot.send_message(message.chat.id, t, reply_markup=markup)
        else:
            msg = bot.send_message(message.chat.id, 'Ошибка! Попробуй написать по другому:')
            bot.register_next_step_handler(msg, search_cat1, category)

    def search_obj_name(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        u_name = '@' + message.from_user.username
        if len(u_text) > 30 or u_text.isdigit() == 1:
            t = 'Слишком длинно для названия! Попробуй написать кратко :)'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)
        if len(u_text) > 2 and u_text.isdigit() == 0:
            cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_id,))
            user_region = cursor.fetchone()[0]
            cursor.execute('INSERT INTO search_obj (u_id, obj_name, u_name, region) VALUES (?, ?, ?, ?)',
                           (u_id, u_text, u_name, user_region))
            conn.commit()
            t = 'Отлично, добавь комментарий к твоему объявлению.\nНапример, можешь написать цену и ' \
                'срок, на который тебе нужна аренда.'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)
        else:
            t = 'Не корректный ввод! Попробуй написать по другому :)'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)

    def search_obj_text(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        if 2 < len(u_text) < 300 and u_text.isdigit() == 0:
            cursor.execute('UPDATE search_obj SET obj_comment = ? WHERE id = (SELECT MAX(id) FROM search_obj WHERE '
                           'u_id = ?)',
                           (u_text, u_id,))
            conn.commit()
            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Всё верно, запускай машину!', callback_data='2-1-1')
            key2 = types.InlineKeyboardButton('Редактировать', callback_data='2-1-0')
            markup.row(key1)
            markup.row(key2)
            cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj WHERE u_id = ?)',
                           (u_id,))
            result = cursor.fetchone()
            reply = bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что :)\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[4], result[2], result[3]),
                                     reply_markup=markup)
            return reply
        else:
            t = 'Не корректный ввод! Попробуй написать по другому :)'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)

    def search_obj_name_edit(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        if len(u_text) > 30 or u_text.isdigit() == 1:
            t = 'Слишком длинно для названия! Попробуй написать кратко :)'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)
        if len(u_text) > 2 and u_text.isdigit() == 0:
            cursor.execute('UPDATE search_obj SET obj_name = ? WHERE id = (SELECT MAX(id) FROM '
                           'search_obj WHERE u_id = ?)',
                           (u_text, u_id,))
            conn.commit()
            cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj WHERE u_id = ?)',
                           (u_id,))
            result = cursor.fetchone()
            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Всё верно, запускай машину!', callback_data='2-1-1')
            key2 = types.InlineKeyboardButton('Редактировать', callback_data='2-1-0')
            markup.row(key1)
            markup.row(key2)
            reply = bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что :)\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[4], result[2], result[3]),
                                     reply_markup=markup)
            return reply
        else:
            t = 'Не корректный ввод! Попробуй написать по другому :)'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)

    # ----------------------------------------ФУНКЦИИ ВЕТКИ СДАТЬ-----------------------------------------------
    # ----------------------------------------РЕДАКТИРОВАНИЕ ОБЬЯВЛЕНИЯ-----------------------------------------
    def update_name_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        name_cat1_obj = message.text
        u_obj_id = message.from_user.id
        if name_cat1_obj.isdigit() == 0:
            cursor.execute('UPDATE obj SET name_cat1_obj = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (name_cat1_obj, u_obj_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[2], result[3], result[4], result[5]),
                                     reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Название не может состоять из цифр. Укажи другое название:')
            bot.register_next_step_handler(msg, update_name_obj)

    def update_money_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        money_cat1 = message.text
        u_obj_id = message.from_user.id
        if money_cat1.isdigit() == 1:
            cursor.execute('UPDATE obj SET money_cat1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (money_cat1, u_obj_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[2], result[3], result[4], result[5]),
                                     reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Укажи цену правильно, например: 100 ')
            bot.register_next_step_handler(msg, update_money_obj)

    def update_text_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        cat_1 = message.text
        u_obj_id = message.from_user.id
        if len(cat_1) > 10 and cat_1.isdigit() == 0:
            cursor.execute('UPDATE obj SET cat_1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (cat_1, u_obj_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[2], result[3], result[4], result[5]),
                                     parse_mode='html', reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введи нормальное описание ;)')
            bot.register_next_step_handler(msg, update_text_obj)

    def update_photo_obj(message):
        if message.content_type == 'photo':
            photo = message.photo[0].file_id
            u_obj_id = message.from_user.id
            cursor.execute('UPDATE obj SET photo = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (photo, u_obj_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            bot.send_photo(message.chat.id, result[6])
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result[2], result[3], result[4], result[5]),
                                     parse_mode='html', reply_markup=markup)
            return reply
        else:
            if message.text.lower() in stop_text:
                t = 'Возвращаю меню...'
                return main_menu(message, t)
            msg = bot.send_message(message.chat.id, 'Ошибка! Отправь фото со сжатием, 1шт.')
            bot.register_next_step_handler(msg, update_photo_obj)

    # ----------------------------------------СОЗДАНИЕ ОБЬЯВЛЕНИЯ---------------------------------------------------
    def init_name_obj(message, z):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        category = '{}'.format(z)
        user_name = '@' + message.from_user.username
        u_text = message.text
        u_obj_id = message.from_user.id
        cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_obj_id,))
        user_region = cursor.fetchone()
        if u_text.isdigit() == 0 and len(u_text) > 2:
            cursor.execute('INSERT INTO obj (u_id, name_cat1_obj, user_name, category, region) VALUES (?, ?, ?, ?, ?)',
                           (u_obj_id, u_text, user_name, category, user_region[0]))
            conn.commit()
            msg = bot.send_message(message.chat.id, 'Понял тебя. Давай теперь определимся с ценой. '
                                                    'Какую сумму за сутки аренды ты бы хотел получить?',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_money_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Название не верного формата. Укажи другое название:')
            bot.register_next_step_handler(msg, init_name_obj, z)

    def init_money_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_obj_money = message.text
        u_obj_id = message.from_user.id
        if u_obj_money.isdigit():
            cursor.execute('UPDATE obj SET money_cat1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (u_obj_money, u_obj_id,))
            conn.commit()
            msg = bot.send_message(message.chat.id, 'Записано! Добавь, пожалуйста, еще описание предмета, '
                                                    'чтобы у соседей не возникало лишних вопросов и чтобы '
                                                    'твой предмет выделялся из множества объявлений. '
                                                    'Достаточно нескольких предложений)',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_photo_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Укажи цену правильно, например: 100 ')
            bot.register_next_step_handler(msg, init_money_obj)

    def init_photo_obj(message):
        if message.text.lower() in stop_text:
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_obj = message.text
        u_obj_id = message.from_user.id
        if len(u_obj) > 10 and u_obj.isdigit() == 0:
            cursor.execute('UPDATE obj SET cat_1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (u_obj, u_obj_id,))
            conn.commit()
            msg = bot.send_message(message.chat.id, 'Почти готово, прикрепи фотографию своего предмета. '
                                                    'Это почти как Тиндер - без фотки никуда)',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введи нормальное описание ;)')
            bot.register_next_step_handler(msg, init_photo_obj)

    def init_obj(message):
        if message.content_type == 'photo':
            u_obj_photo = message.photo[0].file_id
            u_obj_id = message.from_user.id
            cursor.execute('UPDATE obj SET photo = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
                           (u_obj_photo, u_obj_id,))
            conn.commit()

            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, сосед, мы справились! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            bot.send_photo(message.chat.id, result[6])
            reply = bot.send_message(message.chat.id,
                                     "Категория: {}\n\nНазвание: {}\nЦена:{}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?".format(result[7], result[2], result[3], result[4],
                                                                             result[5]),
                                     parse_mode='html', reply_markup=markup)
            return reply
        else:
            print(message)
            msg = bot.send_message(message.chat.id, 'Ошибка! Отправь фото со сжатием, 1шт.')
            bot.register_next_step_handler(msg, init_obj)

    # ---------------------------------------Функия подсчета кол-ва обьявлений в категории------------------------------

    # ------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ/МЕНЮ----------------------------------------
    @bot.message_handler(content_types=['text'])
    def process_start_command(message):
        if message.text == 'Сдать':
            t = 'Здорово, что ты готов сдать что-то в аренду! Я помогу тебе составить объявление. ' \
                'Давай начнем с категории товара, который ты бы хотел сдать в аренду. Выбери подходящее:'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Фото и видео',
                                              callback_data='1-1')
            key2 = types.InlineKeyboardButton('Техника для дома',
                                              callback_data='1-2')
            key3 = types.InlineKeyboardButton('Игры и консоли',
                                              callback_data='1-3')
            key4 = types.InlineKeyboardButton(
                'Туризм и путешествия',
                callback_data='1-4')
            key5 = types.InlineKeyboardButton('Декор и мебель',
                                              callback_data='1-5')
            key6 = types.InlineKeyboardButton('Детские товары',
                                              callback_data='1-6')
            key7 = types.InlineKeyboardButton('Для мероприятий',
                                              callback_data='1-7')
            key8 = types.InlineKeyboardButton('Инструменты',
                                              callback_data='1-8')
            key9 = types.InlineKeyboardButton('Товары для спорта',
                                              callback_data='1-9')
            key10 = types.InlineKeyboardButton('Музыка и хобби',
                                               callback_data='1-10')
            key11 = types.InlineKeyboardButton('Прочее', callback_data='1-11')
            key12 = types.InlineKeyboardButton('Выйти в МЕНЮ', callback_data='menu')
            markup.row(key12)
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key4)
            markup.row(key5)
            markup.row(key6)
            markup.row(key7)
            markup.row(key8)
            markup.row(key9)
            markup.row(key10)
            markup.row(key11)
            bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=markup)

        if message.text == 'Снять':
            u_id = message.from_user.id
            t = 'Понял тебя, арендуем! Уже вспоминанию все объявления твоих соседей! ' \
                'Выбери категорию, в которой находится нужный тебе предмет.'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Фото и видео {}'.format(how_many_obj('Фото и видео', u_id)),
                                              callback_data='2-1')
            key2 = types.InlineKeyboardButton('Техника для дома {}'.format(how_many_obj('Техника для дома', u_id)),
                                              callback_data='2-2')
            key3 = types.InlineKeyboardButton('Игры и консоли {}'.format(how_many_obj('Игры и консоли', u_id)),
                                              callback_data='2-3')
            key4 = types.InlineKeyboardButton(
                'Туризм и путешествия {}'.format(how_many_obj('Туризм и путешествия', u_id)),
                callback_data='2-4')
            key5 = types.InlineKeyboardButton('Декор и мебель {}'.format(how_many_obj('Декор и мебель', u_id)),
                                              callback_data='2-5')
            key6 = types.InlineKeyboardButton('Детские товары {}'.format(how_many_obj('Детские товары', u_id)),
                                              callback_data='2-6')
            key7 = types.InlineKeyboardButton('Для мероприятий {}'.format(how_many_obj('Для мероприятий', u_id)),
                                              callback_data='2-7')
            key8 = types.InlineKeyboardButton('Инструменты {}'.format(how_many_obj('Инструменты', u_id)),
                                              callback_data='2-8')
            key9 = types.InlineKeyboardButton('Товары для спорта {}'.format(how_many_obj('Товары для спорта', u_id)),
                                              callback_data='2-9')
            key10 = types.InlineKeyboardButton('Музыка и хобби {}'.format(how_many_obj('Музыка и хобби', u_id)),
                                               callback_data='2-10')
            key11 = types.InlineKeyboardButton('Прочее {}'.format(how_many_obj('Прочее', u_id)), callback_data='2-11')
            key13 = types.InlineKeyboardButton('Создать объявление о поиске', callback_data='search')
            key12 = types.InlineKeyboardButton('Выйти в МЕНЮ', callback_data='menu')
            markup.row(key12)
            markup.row(key13)
            markup.row(key1)
            markup.row(key2)
            markup.row(key3)
            markup.row(key4)
            markup.row(key5)
            markup.row(key6)
            markup.row(key7)
            markup.row(key8)
            markup.row(key9)
            markup.row(key10)
            markup.row(key11)
            bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=markup)

        if message.text == 'Посмотреть мои обьявления':
            t = 'Какие обьявления смотрим?'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Что я сдаю?', callback_data='3-1-1')
            key2 = types.InlineKeyboardButton('Что я ищу в аренду?', callback_data='3-1-2')
            markup.row(key1)
            markup.row(key2)
            bot.send_message(message.chat.id, t, reply_markup=markup)

        if message.text == 'Меню':
            t = 'Главное Меню'
            main_menu(message, t)

    # ------------------------------------------------------------------------------------------------------------------

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(15)
