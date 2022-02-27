import telebot as tb
from telebot import types
import config
import time
# import sqlite3
import psycopg2
import datetime

import db_obj
from db_obj import *


def main():
    # Подключаемся к боту
    bot = tb.TeleBot(config.TOKEN)
    # Подключаем базу
    # conn = sqlite3.connect('db/database', check_same_thread=False)
    # conn = psycopg2.connect(dbname="sosedi", user='p1', password='123', port=5435)
    # Создаем курсор для работы с таблицами
    # cursor = conn.cursor()
    stop_text = ['нет', 'выход', 'выйти', 'меню', '/menu', '/region', '/start', 'сдать', 'снять', 'посмотреть мои '
                                                                                                  'обьявления',
                 '/notification']

    # Чекаем на наличие стоп слов
    def check_stop_text(mes):
        if mes.text is not None and mes.text.lower() in stop_text:
            return True

    # Чекаем на наличие @юзернейма
    def check_username(message):
        if message.from_user.username is None:
            t = 'Я заметил, что у тебя нет (@ username)! Пожалуйста, добавь его в настройках своего аккаунта. ' \
                'Без этого пользователи бота не смогут с тобой взаимодействовать 😔\n\nКогда добавишь, пиши /start и ' \
                'попробуем ещё раз 👌'
            bot.send_message(message.chat.id, t)
            return 0
        else:
            return message

    # Главное меню
    def main_menu(message, t):
        keyboard_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_menu = ['Сдать', 'Меню', 'Снять', 'Посмотреть мои обьявления']
        keyboard_main.add(button_menu[0], button_menu[1], button_menu[2])
        # keyboard_main.add(button_menu[3])
        bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=keyboard_main)

        markup = types.InlineKeyboardMarkup()
        key1 = types.InlineKeyboardButton('Сдать товар в аренду', callback_data='1')
        key2 = types.InlineKeyboardButton('Арендовать товар', callback_data='2')
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
        ur = user.select(user.user_region).where(user.user_id == u_id)

        res = obj.select(fn.count(obj.category)).where((obj.category == category) & (obj.region == ur)
                                                       & obj.money_cat1.is_null(False) & obj.photo.is_null(False)
                                                       & obj.cat_1.is_null(False)).get()

        # cursor.execute(
        #     'SELECT COUNT(category) FROM obj WHERE category = ? '
        #     'AND region = (SELECT user_region FROM user WHERE user_id = ?)',
        #     (category, u_id,))

        how_many = ((str(res.count)).split(',')[0]).strip('(')
        # print(how_many)
        if how_many == '0':
            return ' '
        else:
            how_many = ' (' + how_many + ')'
            return how_many

    # ------------------------------Функция для регистрации пользователя------------------------------------------------
    def db_table_val(user_id: int, user_name: str, user_region: str, user_registration: int, chat_id: int,
                     d: str):
        u = user.get_or_none((user.chat_id == chat_id) & (user.user_id == user_id))
        if u is None:
            user.create(user_id=user_id, user_name=user_name, user_region=user_region,
                        user_registration=user_registration, chat_id=chat_id, datetime=d)
        else:
            u.user_name = user_name
            u.user_region = user_region
            u.user_registration = user_registration
            user.datetime = d
            u.save()
        # cursor.execute('INSERT OR REPLACE INTO user (user_id, user_name, user_region, user_registration, '
        #                'chat_id, datetime) VALUES (?, ?, ?, ?, ?, ?)',
        #                (user_id, user_name, user_region, user_registration, chat_id, d))
        # conn.commit()

    # --------------------------------------ОБРАБОТЧИК КОМАНДЫ СТАРТ----------------------------------------------------
    @bot.message_handler(commands=['start'])
    def welcome(message):
        # ------------------------ПРОВЕРКА НА НАЛИЧИЕ В БД ПОЛЬЗОВАТЕЛЯ------------------------
        if check_username(message) == 0:
            pass
        else:
            print(message)
            u_id = message.from_user.id
            # info = cursor.execute('SELECT * FROM user WHERE user_id=? AND user_region NOT LIKE ?',
            #                       (u_id, '%undefined%',))
            info = user.get_or_none((user.user_id == u_id) & (~(user.user_region.contains('undefined'))))
            if info is None:
                msg = bot.send_message(message.chat.id,
                                       'Добро пожаловать!\n' +
                                       'Укажи, пожалуйста, свой город.', timeout=10)
                if msg.text:
                    bot.register_next_step_handler(msg, check_city)
            else:
                u_name = message.from_user.first_name
                t = 'Чем займемся сегодня, {}?'.format(u_name)
                main_menu(message, t)

    # notification
    @bot.message_handler(commands=['notification'])
    def notification(message):
        return apply(message)

    # ----------------------APPLY() - О СОГЛАСИИ УВЕДОМЛЕНИЙ--------------------------------
    def apply(message):
        markup = types.InlineKeyboardMarkup()
        key1 = types.InlineKeyboardButton(
            'Только в моём районе',
            callback_data='Yes')
        key2 = types.InlineKeyboardButton('Выбрать несколько районов',
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
                               reply_markup=markup, timeout=10)
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
                   "Бутово", "Бутырский", "Балашиха", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Видное", "Воскресенск", "Гагаринский",
                   "Головинский", "Гольяново", "Даниловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Дзержинский", "Дмитров", "Долгопрудный", "Домодедово",
                   "Дубна", "Егорьевск", "Жуковский", "Замоскворечье", "Зеленоград",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Ивантеевка", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Королёв", "Клин", "Коломна", "Котельники", "Красногорск",
                   "Левобережный", "Лефортово", "Лианозово", "Ломоносовский", "Лобня", "Лосино-петровский",
                   "Лыткарино", "Люберцы", "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово", "Мытищи",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино", "Наро-фоминск", "Ногинск",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Одинцово", "Орехово-зуево",
                   "Перово", "Печатники", "Подольск", "Пушкино",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Раменское", "Реутов", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Сергиев посад", "Серпухов", "Ступино",
                   "Таганский", "Тверской", "Текстильщики", "Тёплый стан", "Троицк",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Фрязино", "Хамовники", "Ховрино", "Хорошёво-мневники", "Химки",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Чехов", "Щукино", "Щёлково", "Щербинка",
                   "Электросталь", "Южнопортовый", "Якиманка", "Ярославский", "Ясенево"]

        for x in get_reg:
            if u_region.lower() == x.lower():
                date = (str(datetime.datetime.now().today()))[:16]
                db_table_val(user_id=u_id, user_name=u_name, user_region=x, user_registration=3, chat_id=chat_id,
                             d=date)
                apply(message)
                break
        else:
            t = 'Не нашёл твой регион, попробуй еще раз. Вот список доступных районов:\n\n{}'.format('\n'.join(get_reg))
            msg = bot.send_message(message.chat.id, t, timeout=10)
            bot.register_next_step_handler(msg, region)

    def check_city(message):
        city = ['москва', 'москвп', 'масква', 'ммасква', 'мск', 'москоу', 'moscow', 'mocscow', 'msc']
        city_korolev = ['королев', 'королёв', 'король', 'каролёв', 'каролев']
        other_city = ['мытищи', 'зеленоград', 'жуковский', 'одинцово', 'балашиха', 'видное', 'воскресенск',
                      'дзержинский', 'дмитров', 'долгопрудный', 'домодедово', 'дубна', 'егорьевск',
                      'ивантеевка', 'клин', 'коломна', 'котельники', 'красногорск', 'лобня', 'лосино-петровский',
                      'лыткарино', 'люберцы', 'наро-фоминск', 'ногинск', 'орехово-зуево',
                      'подольск', 'пушкино', 'раменское', 'реутов', 'сергиев посад', 'серпухов', 'ступино', 'троицк',
                      'фрязино', 'химки', 'чехов', " щёлково", 'электросталь']

        if message.text.lower() in city:
            msg = bot.send_message(message.chat.id,
                                   'Укажи, пожалуйста, свой район, чтобы я мог подключить ' +
                                   'тебя к дружной сети соседей 😉', timeout=10)
            return bot.register_next_step_handler(msg, region)

        if message.text.lower() in city_korolev:
            u_id = message.from_user.id
            chat_id = message.chat.id
            u_name = "@" + message.from_user.username
            u_region = 'Королёв'
            date = (str(datetime.datetime.now().today()))[:16]
            db_table_val(user_id=u_id, user_name=u_name, user_region=u_region, user_registration=2, chat_id=chat_id,
                         d=date)
            # cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            # conn.commit()
            # t = 'Супер! Регистрация завершена, я буду присылать тебе уведомления о поиске в твоем районе, а пока...'
            return apply(message)

        if message.text.lower() in other_city:
            u_id = message.from_user.id
            chat_id = message.chat.id
            u_name = "@" + message.from_user.username
            u_region = message.text.title()
            date = (str(datetime.datetime.now().today()))[:16]
            db_table_val(user_id=u_id, user_name=u_name, user_region=u_region, user_registration=2, chat_id=chat_id,
                         d=date)
            # cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            # conn.commit()
            # t = 'Супер! Регистрация завершена, я буду присылать тебе уведомления о поиске в твоем районе, а пока...'
            return apply(message)
        else:
            u_id = message.from_user.id
            chat_id = message.chat.id
            u_name = "@" + message.from_user.username
            u_region = 'undefined_' + message.text.lower()
            date = (str(datetime.datetime.now().today()))[:16]
            db_table_val(user_id=u_id, user_name=u_name, user_region=u_region, user_registration=1, chat_id=chat_id,
                         d=date)
            with open("city.txt", "a") as file:
                file.write('-' + message.text + '\n')
                file.close()
            bot.send_message(message.chat.id, 'К сожалению, Соседи пока захватывают только Москву и Московскую '
                                              'область. '
                                              '\n\nЕсли ты допустил ошибку в названии, то напиши /start и попробуй '
                                              'ввести '
                                              ' город заново.\n\n'
                                              'В любом случае, я запомнил твой город, чтобы мы скорее могли '
                                              'встретиться!\n '
                                              '\nА пока следи за нашими обновлениями в Instagram:\n'
                                              'https://instagram.com/sosedi.sharing', timeout=10)

    # ------------------------ОБРАБОТЧИК КОМАНДЫ МЕНЮ--------------------------------------------
    @bot.message_handler(commands=['menu'])
    def get_menu(message):
        info = user.get_or_none((user.user_id == message.from_user.id) & ~(user.user_region.contains('undefined')))
        if check_username(message) == 0:
            pass
        elif info is None:
            msg = bot.send_message(message.chat.id,
                                   'Добро пожаловать!\n' +
                                   'Укажи, пожалуйста, свой город.')
            if msg.text:
                bot.register_next_step_handler(msg, check_city)
        else:
            t = 'Возвращаемся к меню...'
            main_menu(message, t)

    # ------------------------ОБРАБОТЧИК КОМАНДЫ СМЕНИТЬ РЕГИОН----------------------------------
    @bot.message_handler(commands=['region'])
    def change_region(message):
        if check_username(message) == 0:
            pass
        else:
            # info = cursor.execute('SELECT * FROM user WHERE user_id=? AND user_region LIKE ?',
            #                       (message.from_user.id, '%undefined%',))
            info = user.get_or_none((user.user_id == message.from_user.id) & (user.user_region ** '%undefined%'))
            if info is None:
                t = 'Хочешь поменять свой район? Введи название района, например: Северный'
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, change_user_region)
            else:
                return welcome(message)

    def change_user_region(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_region = message.text
        u_id = message.from_user.id
        get_reg = ["Академический", "Алексеевский", "Алтуфьевский", "Арбат", "Аэропорт",
                   "Бабушкинский", "Басманный", "Беговой", "Бескудниковский", "Бибирево",
                   "Бирюлёво восточное", "Бирюлёво западное", "Богородское", "Братеево",
                   "Бутово", "Бутырский", "Балашиха", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Видное", "Воскресенск", "Гагаринский",
                   "Головинский", "Гольяново", "Даниловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Дзержинский", "Дмитров", "Долгопрудный", "Домодедово",
                   "Дубна", "Егорьевск", "Жуковский", "Замоскворечье", "Зеленоград",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Ивантеевка", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Королёв", "Клин", "Коломна", "Котельники", "Красногорск",
                   "Левобережный", "Лефортово", "Лианозово", "Ломоносовский", "Лобня", "Лосино-петровский",
                   "Лыткарино", "Люберцы", "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово", "Мытищи",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино", "Наро-фоминск", "Ногинск",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Одинцово", "Орехово-зуево",
                   "Перово", "Печатники", "Подольск", "Пушкино",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Раменское", "Реутов", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Сергиев посад", "Серпухов", "Ступино",
                   "Таганский", "Тверской", "Текстильщики", "Тёплый стан", "Троицк",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Фрязино", "Хамовники", "Ховрино", "Хорошёво-мневники", "Химки",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Чехов", "Щукино", "Щёлково", "Щербинка",
                   "Электросталь", "Южнопортовый", "Якиманка", "Ярославский", "Ясенево"]
        for x in get_reg:
            if u_region.lower() == x.lower():
                user.update({
                    user.user_region: x
                }).where(user.user_id == u_id).execute()
                # cursor.execute('UPDATE user SET user_region = ? WHERE user_id = ?', (x, u_id,))
                # conn.commit()

                obj.update({obj.region: x}).where(obj.u_id == u_id).execute()
                # cursor.execute('UPDATE obj SET region = ? WHERE u_id = ?', (x, u_id,))
                # conn.commit()
                search_obj.update({search_obj.region: x}).where(search_obj.u_id == u_id).execute()
                # cursor.execute('UPDATE search_obj SET region = ? WHERE u_id = ?', (x, u_id,))
                # conn.commit()
                t = 'Я поменял твой район и отредактировал его в твоих обьявлениях! Теперь твой район - {}'.format(x)
                main_menu(message, t)
                break
        else:
            region(message)
            # t = 'Не нашёл такой район.\nПопробуй еще раз.'
            # msg = bot.send_message(message.chat.id, t)
            # bot.register_next_step_handler(msg, change_user_region)
            # main_menu(message, t)

    # -------------------------ОБРАБОТЧИК ВСЕХ КОЛЛ ОТВЕТОВ ОТ ПОЛЬЗОВАТЕЛЯ-----------------------
    @bot.callback_query_handler(func=lambda call: True)
    def apply_get(call):
        message = call.message
        bot.answer_callback_query(call.id)
        if call.data == 'No':
            t = 'Как скажешь! Никаких уведомлений 😌'
            app_num = 3
            u_id = call.from_user.id

            user.update({
                user.user_registration: app_num,
                user.search_message: None  # user.user_region
            }).where(user.user_id == u_id).execute()
            # cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
            #                (app_num, u_id,))
            # conn.commit()

            # cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            # conn.commit()
            bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id,
                                          reply_markup=None)  # удаляем кнопки у последнего сообщения
            main_menu(message, t)
        if call.data == 'Yes':
            app_num = 2
            u_id = call.from_user.id
            # cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
            #                (app_num, u_id,))
            # conn.commit()
            user.update({
                user.user_registration: app_num,
                user.search_message: user.user_region
            }).where(user.user_id == u_id).execute()

            # cursor.execute("UPDATE 'user' SET 'search_message' = user_region WHERE user_id = ?", (u_id,))
            # print(cursor.query)
            # conn.commit()
            bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id,
                                          reply_markup=None)  # удаляем кнопки у последнего сообщения
            t = 'Супер! Договорились, я буду присылать тебе уведомления только о поиске в твоем районе.'
            main_menu(message, t)
        if call.data == 'Yes+':
            app_num = 1
            u_id = call.from_user.id
            user.update({
                user.user_registration: app_num
            }).where(user.user_id == u_id).execute()
            # cursor.execute("UPDATE 'user' SET 'user_registration' = ? WHERE user_id = ?",
            #                (app_num, u_id,))
            # conn.commit()
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
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории ({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-2':
            category = 'Техника для дома'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-3':
            category = 'Игры и консоли'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-4':
            category = 'Туризм и путешествия'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-5':
            category = 'Декор и мебель'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-6':
            category = 'Детские товары'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-7':
            category = 'Для мероприятий'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-8':
            category = 'Инструменты'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-9':
            category = 'Товары для спорта'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-10':
            category = 'Музыка и хобби'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)
        if call.data == '2-11':
            category = 'Прочее'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                t = 'А что именно из ({}) ты бы хотел арендовать? Используй слово или короткую фразу.\n\nЕсли хочешь ' \
                    'посмотреть все объявления, то напиши «все»'.format(category)
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(message.chat.id, t)
                bot.register_next_step_handler(msg, search_cat1, category)

        # ---------------------------------------------------------------------------------------------------
        if call.data == '2-1+':
            t = 'Круто! Тогда смело пиши владельцу 🤝 Он тебя уже ждет!'
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
            bot.delete_message(message.chat.id, message.message_id)
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
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)
        if call.data == '2-1-0-2':
            bot.delete_message(message.chat.id, message.message_id)
            t = 'Введи новое описание'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)

        if call.data == '2-1-1':
            send_push(call)
            t = 'Соседская поисковая машина запущена! Мне понадобится немного времени, ' \
                'но я сообщу сразу, как только найду подходящее для тебя варианты)'
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

            obj.delete().where((obj.u_id == u_id) & (obj.photo.is_null(True)) & (obj.money_cat1.is_null(True)) &
                               (obj.cat_1.is_null(True))).execute()
            # cursor.execute('DELETE FROM obj WHERE u_id = ? AND photo IS NULL OR money_cat1 IS NULL OR cat_1 IS NULL',
            #                (u_id,))
            # conn.commit()
            # cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_comment IS NULL', (u_id,))
            # conn.commit()

            search_obj.delete().where((search_obj.u_id == u_id) & (search_obj.obj_comment.is_null(True))).execute()

            # cursor.execute("SELECT * FROM 'obj' WHERE u_id = ?",
            #                (u_id,))
            # result = cursor.fetchall()
            result = obj.select().where(obj.u_id == u_id).execute()
            if result:
                bot.send_message(message.chat.id,
                                 "Вот все твои действующие объявления: ",
                                 parse_mode='html', timeout=10)
                for x in result:
                    try:
                        bot.send_photo(message.chat.id, x.photo, timeout=10)
                        markup = types.InlineKeyboardMarkup()
                        key1 = types.InlineKeyboardButton('Удалить', callback_data='delete1')
                        markup.row(key1)
                        bot.send_message(message.chat.id,
                                         "Категория: {}\n\nНазвание: {}\n\nЦена:{}р\n\nОписание: {}"
                                         "\n\nВладелец: {}".format(x.category, x.name_cat1_obj, x.money_cat1, x.cat_1,
                                                                   x.user_name),
                                         parse_mode='html', reply_markup=markup, timeout=10)
                    except Exception as ex:
                        print('line 808')
                        print(ex)
            else:
                t = 'Что-то не припомню, чтобы мы с тобой создавали вместе объявление 👀 Хочешь попробовать?'
                main_menu(message, t)

        if call.data == '3-1-2':
            u_id = call.from_user.id
            # cursor.execute('DELETE FROM obj WHERE u_id = ? AND photo IS NULL OR money_cat1 IS NULL OR cat_1 IS NULL',
            #                (u_id,))
            # conn.commit()
            obj.delete().where((obj.u_id == u_id) & obj.photo.is_null(True) & obj.money_cat1.is_null(True)
                               & obj.cat_1.is_null(True)).execute()
            # cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_comment IS NULL', (u_id,))
            # conn.commit()
            search_obj.delete().where((search_obj.u_id == u_id) & search_obj.obj_comment.is_null(True)).execute()
            # cursor.execute("SELECT * FROM 'search_obj' WHERE u_id = ?",
            #                (u_id,))
            # result = cursor.fetchall()
            result = search_obj.select().where(search_obj.u_id == u_id).execute()
            if result:
                bot.send_message(message.chat.id,
                                 "Вот все активные запросы на поиск, которые ты создал: ",
                                 parse_mode='html', timeout=10)
                for x in result:
                    markup = types.InlineKeyboardMarkup()
                    key1 = types.InlineKeyboardButton('Удалить', callback_data='delete2')
                    markup.row(key1)
                    bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что 🔥\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     .format(x.u_name, x.obj_name, x.obj_comment),
                                     reply_markup=markup, timeout=10)
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
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-2':
            print(1)
            category = 'Техника для дома'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                print(2)
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                print(3)
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-3':
            category = 'Игры и консоли'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-4':
            category = 'Туризм и путешествия'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-5':
            category = 'Декор и мебель'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-6':
            category = 'Детские товары'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-7':
            category = 'Для мероприятий'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-8':
            category = 'Инструменты'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-9':
            category = 'Товары для спорта'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-10':
            category = 'Музыка и хобби'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        if call.data == '11-11':
            category = 'Прочее'
            u_id = call.from_user.id
            if how_many_obj(category, u_id) == ' ':
                t = 'В категории({}) нет объявлений, давай создадим запрос на поиск?'.format(category)
                markup = types.InlineKeyboardMarkup()
                key1 = types.InlineKeyboardButton('Давай', callback_data='2-1---')
                key2 = types.InlineKeyboardButton('Нет, спасибо', callback_data='2-1-++')
                markup.row(key1)
                markup.row(key2)
                # bot.send_message(message.chat.id, t, reply_markup=markup)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=t,
                                      reply_markup=markup, timeout=10)
            else:
                # t = 'Ищем в категории {}, все верно?'.format(category)
                # msg = bot.send_message(message.chat.id, t)
                # bot.register_next_step_handler(msg, look_obj, category)
                return look_obj(call, category)

        # ----------ПОСМОТРЕТЬ ВСЕ ОБЪЯВЛЕНИЯ О ПОИСКЕ В АРЕНДУ------------
        if call.data == '77':
            t = 'Вот что сейчас ищут...'
            u_id = call.from_user.id
            # cursor.execute("SELECT user_region FROM 'user' WHERE user_id = ?", (u_id,))
            # user_region = cursor.fetchone()
            user_region = user.select(user.user_region).where(user.user_id == u_id)
            # cursor.execute("SELECT * FROM 'search_obj' WHERE obj_comment IS NOT NULL AND region = ?",
            #                (user_region[0],))
            # result = cursor.fetchall()
            result = search_obj.select().where(search_obj.obj_comment.is_null(False) &
                                               (search_obj.region == user_region)).execute()
            if result:
                bot.send_message(message.chat.id, t)
                for x in result:
                    bot.send_message(message.chat.id,
                                     "{} - срочно ищет кое-что 🔥\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     .format(x.u_name, x.obj_name, x.obj_comment), timeout=10)
            else:
                t = 'В твоём районе нет активных запросов на поиск.'
                main_menu(message, t)

        # -----СДАТЬ В КАТЕГОРИИ -----
        if call.data == '1-1':
            t = 'Супер! А что именно из категории (Фото и видео) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Фото и видео'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-2':
            t = 'Супер! А что именно из категории (Техника для дома) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Техника для дома'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-3':
            t = 'Супер! А что именно из категории (Игры и консоли) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Игры и консоли'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-4':
            t = 'Супер! А что именно из категории (Туризм и путешествия) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Туризм и путешествия'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-5':
            t = 'Супер! А что именно из категории (Декор и мебель) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Декор и мебель'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-6':
            t = 'Супер! А что именно из категории (Детские товары) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Детские товары'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-7':
            t = 'Супер! А что именно из категории (Для мероприятий) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Для мероприятий'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-8':
            t = 'Супер! А что именно из категории (Инструменты) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Инструменты'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-9':
            t = 'Супер! А что именно из категории (Товары для спорта) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Товары для спорта'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-10':
            t = 'Супер! А что именно из категории (Музыка и хобби) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Музыка и хобби'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        if call.data == '1-11':
            t = 'Супер! А что именно из категории (Прочее) ты готов сдать в аренду? ' \
                'Укажи название, нескольких слов будет достаточно 👌\n\n‼️ Важно: объявления создаются по одному'
            z = 'Прочее'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, init_name_obj, z)

        # -----ПОДТВЕРДИТЬ ТОЛЬКО ЧТО СОЗДАННОЕ ОБЬЯВЛЕНИЕ(КАТ_1)------
        if call.data == '01':
            t = 'Супер! Объявление добавлено.\n\n‼️ Важно: перед сдачей в аренду изучи правила, которые помогут ' \
                'избежать конфликтов: https://telegra.ph/Osnovy-bezopasnoj-sdelki-12-13'
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
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_id)
            obj.delete().where(obj.id == m).execute()
            # cursor.execute('DELETE FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (u_id,))
            # conn.commit()
            t = 'Я удалил твоё последнее объявление.\n'
            main_menu(message, t)
        if call.data == '01-1-1':
            t = 'Введи НОВОЕ название объявления'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_name_obj)
        if call.data == '01-1-2':
            t = 'Введи НОВУЮ цену объявления'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_money_obj)
        if call.data == '01-1-3':
            t = 'Введи НОВОЕ описание объявления'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_text_obj)
        if call.data == '01-1-5':
            t = 'Отправь НОВУЮ фотографию для объявления'
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(message.chat.id, t, parse_mode='html')
            bot.register_next_step_handler(msg, update_photo_obj)

        # --------УДАЛИТЬ ОБЬЯВЛЕНИЕ----------------------------------------
        if call.data == 'delete1':
            t = 'Введи название своего обьявления, которое ты хочешь удалить.'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, delete_obj)
            return

        if call.data == 'delete2':
            t = 'Введи название своего обьявления, которое ты хочешь удалить.'

            msg = bot.send_message(message.chat.id, t, timeout=10)
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
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_reg = message.text
        u_region = [str(x) for x in u_reg.split(', ')]
        u_id = message.from_user.id
        get_reg = ["Академический", "Алексеевский", "Алтуфьевский", "Арбат", "Аэропорт",
                   "Бабушкинский", "Басманный", "Беговой", "Бескудниковский", "Бибирево",
                   "Бирюлёво восточное", "Бирюлёво западное", "Богородское", "Братеево",
                   "Бутово", "Бутырский", "Балашиха", "Вешняки",
                   "Внуково", "Войковский", "Восточный", "Выхино-жулебино", "Видное", "Воскресенск", "Гагаринский",
                   "Головинский", "Гольяново", "Даниловский", "Дегунино восточное", "Дегунино западное",
                   "Дмитровский", "Донской", "Дорогомилово", "Дзержинский", "Дмитров", "Долгопрудный", "Домодедово",
                   "Дубна", "Егорьевск", "Жуковский", "Замоскворечье", "Зеленоград",
                   "Зюзино", "Зябликово", "Ивановское", "Измайлово восточное", "Измайлово",
                   "Измайлово северное", "Ивантеевка", "Капотня", "Коньково", "Коптево", "Косино-ухтомский",
                   "Котловка", "Красносельский", "Крылатское", "Крюково", "Кузьминки",
                   "Кунцево", "Куркино", "Королёв", "Клин", "Коломна", "Котельники", "Красногорск",
                   "Левобережный", "Лефортово", "Лианозово", "Ломоносовский", "Лобня", "Лосино-петровский",
                   "Лыткарино", "Люберцы", "Лосиноостровский", "Люблино", "Марфино", "Марьина роща", "Марьино",
                   "Матушкино", "Медведково", "Метрогородок",
                   "Мещанский", "Митино", "Можайский", "Молжаниновский", "Москворечье-сабурово", "Мытищи",
                   "Нагатино-садовники", "Нагатинский затон", "Нагорный", "Некрасовка",
                   "Нижегородский", "Ново-переделкино", "Новогиреево", "Новокосино", "Наро-фоминск", "Ногинск",
                   "Обручевский", "Орехово-борисово северное", "Орехово-борисово южное",
                   "Останкинский", "Отрадное", "Очаково-матвеевское", "Одинцово", "Орехово-зуево",
                   "Перово", "Печатники", "Подольск", "Пушкино",
                   "Покровское-стрешнево", "Преображенское", "Пресненский", "Проспект вернадского",
                   "Раменки", "Ростокино", "Рязанский", "Раменское", "Реутов", "Савёлки", "Савёловский", "Свиблово",
                   "Северный", "Силино", "Сокол", "Соколиная гора", "Сокольники", "Солнцево",
                   "Старое крюково", "Строгино", "Сергиев посад", "Серпухов", "Ступино",
                   "Таганский", "Тверской", "Текстильщики", "Тёплый стан", "Троицк",
                   "Тимирязевский", "Тропарёво-никулино", "Тушино северное", "Тушино южное",
                   "Филёвский парк", "Фили-давыдково", "Фрязино", "Хамовники", "Ховрино", "Хорошёво-мневники", "Химки",
                   "Хорошёвский", "Царицыно", "Черёмушки", "Чертаново", "Чехов", "Щукино", "Щёлково", "Щербинка",
                   "Электросталь", "Южнопортовый", "Якиманка", "Ярославский", "Ясенево"]
        # cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_id,))
        # result = cursor.fetchone()
        result = user.select(user.user_region).where(user.user_id == u_id).get_or_none()
        # if result.user_region:
        #     u_region.append(result.user_region)
        if set(u_region).issubset(get_reg) == 1:
            result = ", ".join(list(set(get_reg).intersection(set(u_region))))
            user.update({
                user.search_message: result
            }).where(user.user_id == u_id).execute()
            # cursor.execute('UPDATE user SET search_message = ? WHERE user_id = ?', (result, u_id,))
            # conn.commit()
            t = 'Понял тебя. Теперь буду сообщать тебе о поиске в этих районах: {}'.format(result)
            main_menu(message, t)
        else:
            t = 'Не нашёл все районы, пожалуйста, попробуй еще раз.\n' \
                'Ввод должен быть таким: Арбат, Царицыно, Внуково\n\n' \
                'Вот список доступных районов:\n\n{}' \
                .format('\n'.join(get_reg))
            msg = bot.send_message(message.chat.id, t, timeout=10)
            bot.register_next_step_handler(msg, search_message_init)

    # -----------------ФУНКЦИЯ ДЛЯ ПРОСМОТРА ВСЕХ ОБ. ПО КАТЕГОРИЯМ И РЕГИОНУ ПОЛЬЗОВАТЕЛЯ----------------------
    def look_obj(message, category):
        # if message.text.lower() in stop_text:
        #     t = 'Возвращаю меню...'
        #     return main_menu(message, t)
        # if message[2] == 'from_user':
        #     u_id =
        u_id = message.from_user.id
        # cursor.execute("SELECT user_region FROM user WHERE user_id = ?", (u_id,))
        # u_region = cursor.fetchone()
        u_region = user.select(user.user_region).where(user.user_id == u_id)
        cat = '{}'.format(category)
        # cursor.execute("SELECT * FROM 'obj' WHERE "
        #                "cat_1 IS NOT NULL AND name_cat1_obj IS NOT NULL AND photo IS NOT NULL "
        #                "AND category = ? AND region = ?", (cat, u_region[0],))
        # result = cursor.fetchall()
        result = obj.select().where(
            obj.cat_1.is_null(False) &
            obj.name_cat1_obj.is_null(False) &
            obj.photo.is_null(False) &
            (obj.category == cat) &
            (obj.region == u_region))

        if result:
            bot.send_message(message.from_user.id,
                             "Вот все действующие объявления: ",
                             parse_mode='html', timeout=10)
            for x in result:
                bot.send_photo(message.from_user.id, x.photo)
                bot.send_message(message.from_user.id,
                                 "Категория: {}\n\nНазвание: {}\n\nЦена: {}р\n\nОписание :{}"
                                 "\n\nВладелец:{}".format(x.category, x.name_cat1_obj, x.money_cat1, x.cat_1,
                                                          x.user_name),
                                 parse_mode='html', timeout=10)
            t = 'Нашел ли ты нужное или все не то?\n\n‼️ Важно: перед арендой изучи правила, которые помогут избежать ' \
                'конфликтов: https://telegra.ph/Osnovy-bezopasnoj-sdelki-12-13'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Подходит!', callback_data='2-1+')
            key2 = types.InlineKeyboardButton('Я не нашёл, что искал', callback_data='2-1-')
            markup.row(key1)
            markup.row(key2)
            bot.send_message(message.from_user.id, t, reply_markup=markup, timeout=10)
        else:
            t = 'Похоже, еще никто не создал объявление 😔'
            main_menu(message, t)

    # ------------------------------ФУНКЦИИ ДЛЯ УДАЛЕНИЯ ОБЬЯВЛЕНИЙ-------------------------------------
    def delete_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_id = message.from_user.id
        u_text = message.text
        # cursor.execute('SELECT name_cat1_obj FROM obj WHERE u_id = ?', (u_id,))
        # result = cursor.fetchall()
        result = obj.select(obj.name_cat1_obj).where(obj.u_id == u_id)
        for x in result:
            # a = x[0]
            a = x.name_cat1_obj
            if u_text.lower() == a.lower():
                obj.delete().where((obj.u_id == u_id) & (obj.name_cat1_obj == a)).execute()
                # cursor.execute('DELETE FROM obj WHERE u_id = ? AND name_cat1_obj = ?', (u_id, a,))
                # conn.commit()
                t = 'Я удалил обьявление ({})'.format(a)
                bot.send_message(message.chat.id, t, timeout=10)
                break
        else:
            t = 'Я не нашел в списке твоих обьявлений такое название.'
            bot.send_message(message.chat.id, t, timeout=10)

    def delete_search_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_id = message.from_user.id
        u_text = message.text
        # cursor.execute('SELECT obj_name FROM search_obj WHERE u_id = ?', (u_id,))
        # result = cursor.fetchall()
        result = search_obj.select(search_obj.obj_name).where(search_obj.u_id == u_id)
        for x in result:
            # a = x[0]
            a = x.obj_name
            if u_text.lower() == a.lower():
                # cursor.execute('DELETE FROM search_obj WHERE u_id = ? AND obj_name = ?', (u_id, a,))
                # conn.commit()
                search_obj.delete().where((search_obj.u_id == u_id) & (search_obj.obj_name == a)).execute()
                t = 'Я удалил обьявление {}'.format(a)
                bot.send_message(message.chat.id, t, timeout=10)
                break
        else:
            t = 'Я не нашел в списке твоих обьявлений такое название.'
            bot.send_message(message.chat.id, t)

    # --------------------------------------ФУНКЦИЯ ДЛЯ УВЕДОМЛЕНИЯ---------------------------------------------
    def send_push(message):
        u1_id = message.from_user.id
        # cursor.execute('SELECT user_region FROM user WHERE user_id = ?',
        #                (u1_id,))
        # u1_region = cursor.fetchall()
        u1_region = user.select(user.user_region).where(user.user_id == u1_id).execute()
        # cursor.execute('SELECT chat_id FROM user WHERE user_registration = ? OR user_registration = ?',
        #                (1, 2))
        # u2_id = cursor.fetchall()
        u2_id = user.select(user.chat_id).where((user.user_registration == 1) | (user.user_registration == 2)).execute()
        if u2_id and u1_region:
            for x in u2_id:
                # cursor.execute('SELECT search_message FROM user WHERE user_id = ?',
                #                (x[0],))
                # region_lst = cursor.fetchall()
                region_lst = user.select(user.search_message).where(user.user_id == x.chat_id).execute()
                if region_lst:
                    if u1_region[0].user_region in region_lst[0].search_message:
                        # if u1_region[0][0] in region_lst[0][0]:
                        #     cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj '
                        #                    'WHERE u_id = ?)', (u1_id,))
                        #     result = cursor.fetchone()
                        m = search_obj.select(fn.max(search_obj.id)).where(search_obj.u_id == u1_id)
                        try:
                            result = search_obj.select().where(search_obj.id == m).get()

                            bot.send_message(x.chat_id,
                                             "Всем привет!\n{} - срочно ищет кое-что 🔥\n\n"
                                             "Название: {}\n\nОписание: {}\n\n"
                                             .format(result.u_name, result.obj_name, result.obj_comment), timeout=10)
                            # .format(result[4], result[2], result[3]))
                        except Exception as e:
                            print(e)
        else:
            return 0

    # ----------------------------------------ФУНКЦИИ ВЕТКИ СЬЕМ------------------------------------------------

    def search_cat1(message, category):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        all_search = ['все', 'всё', 'все обьявления', 'все объявления', 'обьявления', 'обьявление', 'объявления',
                      'объявление', 'объявление все', 'посмотреть все', 'посмотреть всё', 'all']
        if message.text.lower() in all_search:
            return look_obj(message, category)
        u_text = message.text
        u_id = message.from_user.id
        cat = '{}'.format(category)
        # cursor.execute("SELECT user_region FROM user WHERE user_id = ?", (u_id,))
        # u_region = cursor.fetchone()
        u_r = user.get(user.user_id == u_id)

        # cursor.execute("SELECT * FROM 'obj' WHERE "
        #                "cat_1 IS NOT NULL AND name_cat1_obj IS NOT NULL AND photo IS NOT NULL "
        #                "AND category = ? AND region = ?", (cat, u_region[0],))
        # result = cursor.fetchall()
        result = obj.select().where(
            (obj.cat_1.is_null(False)) &
            (obj.name_cat1_obj.is_null(False)) &
            (obj.photo.is_null(False)) &
            (obj.category == cat) &
            (obj.region == u_r.id))

        if u_text is not None and len(u_text) > 2 and u_text.isdigit() == 0:
            r = 0
            for x in result:
                # a = x[2]
                a = x.name_cat1_obj
                if u_text.lower() in a.lower():
                    bot.send_message(message.chat.id, 'Смотри, что я нашел!')
                    bot.send_photo(message.chat.id, x.photo, timeout=10)
                    bot.send_message(message.chat.id, 'Название: {}\n\nЦена: {}р\n\nОписание: {}\n\nВладелец: {}'
                                     .format(x.name_cat1_obj, x.money_cat1, x.cat_1, x.user_name))
                    r = r + 1
            if r != 0:
                t = 'Нашел ли ты нужное или все не то?\n\n‼️ Важно: перед арендой изучи правила, которые помогут ' \
                    'избежать конфликтов: https://telegra.ph/Osnovy-bezopasnoj-sdelki-12-13'
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
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        u_name = '@' + message.from_user.username
        date = (str(datetime.datetime.now().today()))[:16]
        if u_text is None:
            t = 'Некорректный ввод! Попробуй написать по другому 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)
        elif len(u_text) > 30 or u_text.isdigit() == 1:
            t = 'Слишком длинно для названия! Попробуй написать кратко 🙏'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)
        elif len(u_text) > 2 and u_text.isdigit() == 0:
            # cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_id,))
            # user_region = cursor.fetchone()[0]

            u = user.select(user.user_region).where(user.user_id == u_id).get()

            # cursor.execute('INSERT INTO search_obj (u_id, obj_name, u_name, region, datetime) VALUES (?, ?, ?, ?, ?)',
            #                (u_id, u_text, u_name, user_region, date))
            # conn.commit()
            ins = search_obj.insert({
                search_obj.u_id: u_id,
                search_obj.obj_name: u_text,
                search_obj.u_name: u_name,
                search_obj.region: u.user_region,
                search_obj.datetime: date
            }).execute()

            t = 'Отлично, добавь комментарий к твоему объявлению.\nНапример, можешь написать цену и ' \
                'срок, на который тебе нужна аренда.'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)
        else:
            t = 'Некорректный ввод! Попробуй написать по другому 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name)

    def search_obj_text(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        if u_text is not None and 2 < len(u_text) < 300 and u_text.isdigit() == 0:
            m = search_obj.select(fn.max(search_obj.id)).where(search_obj.u_id == u_id)
            # cursor.execute('UPDATE search_obj SET obj_comment = ? WHERE id = (SELECT MAX(id) FROM search_obj WHERE '
            #                'u_id = ?)',
            #                (u_text, u_id,))
            # conn.commit()
            search_obj.update({search_obj.obj_comment: u_text}).where(search_obj.id == m).execute()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Всё верно, запускай машину!', callback_data='2-1-1')
            key2 = types.InlineKeyboardButton('Редактировать', callback_data='2-1-0')
            markup.row(key1)
            markup.row(key2)
            # cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj WHERE u_id = ?)',
            #                (u_id,))
            # result = cursor.fetchone()
            maxid = m.get()
            result = search_obj.get_by_id(maxid.max)

            reply = bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что 🔥\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.u_name, result.obj_name, result.obj_comment),
                                     reply_markup=markup)
            return reply
        else:
            t = 'Некорректный ввод! Попробуй написать по другому 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_text)

    def search_obj_name_edit(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_text = message.text
        u_id = message.from_user.id
        if u_text is None:
            t = 'Некорректный ввод! Попробуй написать по другому 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)
        elif len(u_text) > 30 or u_text.isdigit() == 1:
            t = 'Слишком длинно для названия! Попробуй написать кратко 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)
        elif len(u_text) > 2 and u_text.isdigit() == 0:
            m = search_obj.select(fn.max(search_obj.id)).where(search_obj.u_id == u_id)
            search_obj.update({search_obj.obj_name: u_text}).where(search_obj.id == m).execute()
            # cursor.execute('UPDATE search_obj SET obj_name = ? WHERE id = (SELECT MAX(id) FROM '
            #                'search_obj WHERE u_id = ?)',
            #                (u_text, u_id,))
            # conn.commit()
            # cursor.execute('SELECT * FROM search_obj WHERE id = (SELECT MAX(id) FROM search_obj WHERE u_id = ?)',
            #                (u_id,))
            # result = cursor.fetchone()
            result = search_obj.select().where(search_obj.id == m).get()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Всё верно, запускай машину!', callback_data='2-1-1')
            key2 = types.InlineKeyboardButton('Редактировать', callback_data='2-1-0')
            markup.row(key1)
            markup.row(key2)
            reply = bot.send_message(message.chat.id,
                                     "Всем привет!\n{} - срочно ищет кое-что 🔥\n\n"
                                     "Название: {}\n\nОписание: {}\n\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.u_name, result.obj_name, result.obj_comment),
                                     reply_markup=markup)
            return reply
        else:
            t = 'Некорректный ввод! Попробуй написать по другому 😔'
            msg = bot.send_message(message.chat.id, t)
            bot.register_next_step_handler(msg, search_obj_name_edit)

    # ----------------------------------------ФУНКЦИИ ВЕТКИ СДАТЬ-----------------------------------------------
    # ----------------------------------------РЕДАКТИРОВАНИЕ ОБЬЯВЛЕНИЯ-----------------------------------------
    def update_name_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        name_cat1_obj = message.text
        u_obj_id = message.from_user.id
        if name_cat1_obj.isdigit() == 0:
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            obj.update({obj.name_cat1_obj: name_cat1_obj}).where(obj.id == m).execute()
            # cursor.execute('UPDATE obj SET name_cat1_obj = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (name_cat1_obj, u_obj_id,))
            # conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            # cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            # result = cursor.fetchone()
            result = obj.select().where(obj.id == m).get()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.name_cat1_obj, result.money_cat1, result.cat_1, result.user_name),
                                     reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Название не может состоять из цифр. Укажи другое название:')
            bot.register_next_step_handler(msg, update_name_obj)

    def update_money_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        money_cat1 = message.text
        u_obj_id = message.from_user.id
        if money_cat1.isdigit() == 1:
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            obj.update({obj.money_cat1: money_cat1}).where(obj.id == m).execute()
            # cursor.execute('UPDATE obj SET money_cat1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (money_cat1, u_obj_id,))
            # conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            # cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            # result = cursor.fetchone()
            result = obj.select().where(obj.id == m).get()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.name_cat1_obj, result.money_cat1, result.cat_1, result.user_name),
                                     reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Укажи цену правильно, например: 100 ')
            bot.register_next_step_handler(msg, update_money_obj)

    def update_text_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        cat_1 = message.text
        u_obj_id = message.from_user.id
        if len(cat_1) > 10 and cat_1.isdigit() == 0:
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            # cursor.execute('UPDATE obj SET cat_1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (cat_1, u_obj_id,))
            # conn.commit()
            obj.update({obj.cat_1: cat_1}).where(obj.id == m).execute()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            # cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            # result = cursor.fetchone()
            result = obj.select().where(obj.id == m).get()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.name_cat1_obj, result.money_cat1, result.cat_1, result.user_name),
                                     parse_mode='html', reply_markup=markup)
            return reply
        else:
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введи нормальное описание ;)')
            bot.register_next_step_handler(msg, update_text_obj)

    def update_photo_obj(message):
        if message.content_type == 'photo':
            photo = message.photo[0].file_id
            u_obj_id = message.from_user.id
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            obj.update({
                obj.photo: photo
            }).where(obj.id == m).execute()
            # cursor.execute('UPDATE obj SET photo = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (photo, u_obj_id,))
            # conn.commit()
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            # cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            # result = cursor.fetchone()
            result = obj.select().where(obj.id == m).get()

            bot.send_message(message.chat.id, "Итак, проверим еще раз! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html')
            bot.send_photo(message.chat.id, result.photo)
            reply = bot.send_message(message.chat.id,
                                     "Название: {}\nЦена: {}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?"
                                     .format(result.name_cat1_obj, result.money_cat1, result.cat_1, result.user_name),
                                     parse_mode='html', reply_markup=markup)
            return reply
        else:
            if check_stop_text(message):
                t = 'Возвращаю меню...'
                return main_menu(message, t)
            msg = bot.send_message(message.chat.id, 'Ошибка! Отправь фото со сжатием, 1шт.')
            bot.register_next_step_handler(msg, update_photo_obj)

    # ----------------------------------------СОЗДАНИЕ ОБЬЯВЛЕНИЯ---------------------------------------------------
    def init_name_obj(message, z):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        category = '{}'.format(z)
        user_name = '@' + message.from_user.username
        u_text = message.text
        u_obj_id = message.from_user.id
        date = (str(datetime.datetime.now().today()))[:16]
        # cursor.execute('SELECT user_region FROM user WHERE user_id = ?', (u_obj_id,))
        # user_region = cursor.fetchone()
        u = user.get_or_none(user.user_id == u_obj_id)
        if u_text is None:
            msg = bot.send_message(message.chat.id, 'Вы не ввели название.!')
            bot.register_next_step_handler(msg, init_name_obj, z)
        elif u_text.isdigit() == 0 and len(u_text) > 2:
            # cursor.execute('INSERT INTO obj (u_id, name_cat1_obj, user_name, category, region, datetime) '
            #                'VALUES (?, ?, ?, ?, ?, ?)',
            #                (u_obj_id, u_text, user_name, category, user_region[0], date))
            # conn.commit()
            obj.insert({
                obj.u_id: u_obj_id,
                obj.name_cat1_obj: u_text,
                obj.user_name: user_name,
                obj.category: category,
                obj.region: u.user_region,
                obj.datetime: date
            }).execute()
            msg = bot.send_message(message.chat.id, 'Понял тебя. Давай теперь определимся с ценой. '
                                                    'Какую сумму за сутки аренды ты бы хотел получить?',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_money_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Название не верного формата. Укажи другое название:')
            bot.register_next_step_handler(msg, init_name_obj, z)

    def init_money_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_obj_money = message.text
        u_obj_id = message.from_user.id
        if u_obj_money is not None and u_obj_money.isdigit():
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            obj.update({
                obj.money_cat1: u_obj_money
            }).where(obj.id == m).execute()
            # cursor.execute('UPDATE obj SET money_cat1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (u_obj_money, u_obj_id,))
            # conn.commit()
            msg = bot.send_message(message.chat.id, 'Записано! Добавь, пожалуйста, еще описание предмета, '
                                                    'чтобы у соседей не возникало лишних вопросов (модель, размер, состояние и другие характеристики). '
                                                    'Достаточно нескольких предложений)',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_photo_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Укажи цену правильно, например: 100 ')
            bot.register_next_step_handler(msg, init_money_obj)

    def init_photo_obj(message):
        if check_stop_text(message):
            t = 'Возвращаю меню...'
            return main_menu(message, t)
        u_obj = message.text
        u_obj_id = message.from_user.id
        if u_obj is None:
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введи нормальное описание ;)')
            bot.register_next_step_handler(msg, init_photo_obj)
        elif len(u_obj) > 10 and u_obj.isdigit() == 0:
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            q = obj.update({obj.cat_1: u_obj}).where(obj.id == m).execute()

            # cursor.execute('UPDATE obj SET cat_1 = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (u_obj, u_obj_id,))
            # conn.commit()
            msg = bot.send_message(message.chat.id, 'Почти готово, прикрепи фотографию своего предмета. '
                                                    'Это почти как Тиндер - без фотки никуда.\n\nЕсли сейчас нет возможности сделать фото, то возьми из интернета.\n‼️ Без фото объявление не будет опубликовано ‼️',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, init_obj)
        else:
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введи нормальное описание ;)')
            bot.register_next_step_handler(msg, init_photo_obj)

    def init_obj(message):
        if message.content_type == 'photo':
            u_obj_photo = message.photo[0].file_id
            u_obj_id = message.from_user.id
            #####################
            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            obj.update({
                obj.photo: u_obj_photo
            }).where(obj.id == m).execute()
            ################################### Поправить БД
            # cursor.execute('UPDATE obj SET photo = ? WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)',
            #                (u_obj_photo, u_obj_id,))
            # conn.commit()

            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Редактировать', callback_data='01-1')
            key2 = types.InlineKeyboardButton('Всё ОК!', callback_data='01')
            markup.row(key1)
            markup.row(key2)

            m = obj.select(fn.max(obj.id)).where(obj.u_id == u_obj_id)
            result = obj.select().where(obj.id == m).get_or_none()
            # cursor.execute('SELECT * FROM obj WHERE id = (SELECT MAX(id) FROM obj WHERE u_id = ?)', (u_obj_id,))
            # result = cursor.fetchone()

            bot.send_message(message.chat.id, "Итак, сосед, мы справились! Смотри какое "
                                              "объявление у нас получилось: ",
                             parse_mode='html', timeout=10)
            bot.send_photo(message.chat.id, result.photo)
            reply = bot.send_message(message.chat.id,
                                     "Категория: {}\n\nНазвание: {}\nЦена:{}р\nОписание: {}\nВладелец: {}\n"
                                     "Все ли я понял правильно или хочешь "
                                     "что-то исправить в объявлении?".format(result.category, result.name_cat1_obj,
                                                                             result.money_cat1, result.cat_1,
                                                                             result.user_name),
                                     parse_mode='html', reply_markup=markup, timeout=10)
            return reply
        else:
            print(message)
            msg = bot.send_message(message.chat.id, 'Ошибка! Отправь фото со сжатием, 1шт.', timeout=10)
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
            bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=markup, timeout=10)

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
            bot.send_message(message.chat.id, t, parse_mode='html', reply_markup=markup, timeout=10)

        if message.text == 'Посмотреть мои обьявления':
            t = 'Какие обьявления смотрим?'
            markup = types.InlineKeyboardMarkup()
            key1 = types.InlineKeyboardButton('Что я сдаю?', callback_data='3-1-1')
            key2 = types.InlineKeyboardButton('Что я ищу в аренду?', callback_data='3-1-2')
            markup.row(key1)
            markup.row(key2)
            bot.send_message(message.chat.id, t, reply_markup=markup, timeout=10)

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

    # bot.polling(none_stop=True, timeout=150)
    # bot.infinity_polling()


if __name__ == "__main__":
    try:
        main()
    finally:
        psql_db.close()
