"""
Телеграм-бот для изучения английского языка. Предлагает различные варианты слов и проверять их правильный перевод
Телеграм-бот разделен на две части. В части "Обучение" предлагается слово на русском языке и 4 варианта на английском языке.
Необходимо выбрать правильный вариант ответа, чтобы продвинуться в изучении слова
В части "Настройки" предлагается возможность доабления новых слов в словарь пользователя, удаления слов и просмотр статистики

----

В модуле импортированы: 
random,
telebot (методы TeleBot, types, custom_filters),
telebot.handler_backends (методы State, StatesGroup), 
telebot.storage (метод StateMemoryStorage)
config, db_bot, YandexDict, Example

"""

import random
from telebot import TeleBot, types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
import config
import db_bot
from YandexDict import *
from Example import *

bot = TeleBot(config.token_bot, state_storage=StateMemoryStorage())
print('Запуск бота...')


# "Состояния" для реализации возможности восприятия программой слов, которые вводит пользователь
user_step = {}
class MyStates(StatesGroup):
    education = State()
    add_word = State()
    del_word = State()


# Главное меню
@bot.message_handler(commands=['start'])
def start_message(message):
    """Вывод приветственного сообщения и двух кнопок: 'Начать обучение' и 'Настройки'"""
    user_step[message.chat.id] = 'start'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_btn = types.KeyboardButton('Начать обучение')
    stat_btn = types.KeyboardButton('Настройки')
    markup.add(start_btn, stat_btn)
    if db_bot.check_user(message.from_user.id) is False:
        db_bot.add_user(message.from_user.id)
    bot.send_message(message.chat.id,
                     text='Привет 👋, {0.first_name}! Давай попрактикуемся в английском языке. \n '
                          'Обучение можете проходить в удобном для Вас темпе. У Вас есть возможность '
                          'использовать тренажёр как конструктор и собирать свою собственную базу для '
                          'обучения.'.format(message.from_user), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Главное меню')
def back_menu(message):
    """Кнопка возврата в главное меню"""
    start_message(message)


@bot.message_handler(func=lambda message: message.text == 'Начать обучение')
def education(message):
    """
    Раздел "Обучение". Здесь происходит выборка слов из общего словаря (general_dict) и словаря пользователя
    (user_dict) с учетом их изученности (не более 5 верных угадываний). 
    Случайным образом (random) выбирается слово из совокупной выборки слов, правильный перевод слова и 3 случайных слова.
    Эти слова записываются в переменную data и затем подаются для обработки в функцию check_word.
    """
    user_step[message.chat.id] = 'education'
    user_words_db_list = db_bot.get_study_words(message.from_user.id)
    gen_words_db_list = [el for el in db_bot.get_words_gd() if el not in db_bot.get_words(message.from_user.id)]
    words_dict = {word[0]: word[1] for word in (gen_words_db_list + user_words_db_list)}
    # print(words_dict)
    target_word = random.choice(list(words_dict.keys()))
    target_word_trans = words_dict[target_word]
    random_words_dict = words_dict.copy()
    random_words_dict.pop(target_word)
    random_words_trans = random.sample(list(random_words_dict.values()), 3)
    markup_education = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = []
    target_word_trans_btn = types.KeyboardButton(target_word_trans)
    random_words_trans_btn = [types.KeyboardButton(word) for word in random_words_trans]
    btns.append(target_word_trans_btn)
    btns.extend(random_words_trans_btn)
    random.shuffle(btns)
    next_word_btn = types.KeyboardButton('Следующее слово')
    back_menu_btn = types.KeyboardButton('Главное меню')
    btns.extend([next_word_btn, back_menu_btn])
    markup_education.add(*btns)
    bot.send_message(message.chat.id, text=f'Выбери перевод слова:\n{target_word}', 
                     reply_markup=markup_education) 
    bot.set_state(message.from_user.id, MyStates.education, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['target_word_trans'] = target_word_trans
        data['random_words_trans'] = random_words_trans


@bot.message_handler(func=lambda message: message.text == 'Настройки')
def preferences(message):
    """
    Раздел "Настройки". Выввод информационного сообщения с указанием возможностей и функциональных кнопок.
    """
    user_step[message.chat.id] = 'preferences'
    markup_pref = types.ReplyKeyboardMarkup(resize_keyboard=True)
    add_word_btn = types.KeyboardButton('Добавить слово')
    del_word_btn = types.KeyboardButton('Удалить слово')
    stat_btn = types.KeyboardButton('Статистика')
    back_menu_btn = types.KeyboardButton('Главное меню')
    markup_pref.add(add_word_btn, del_word_btn, stat_btn, back_menu_btn)
    bot.send_message(message.chat.id,
                     text=f'В этом меню Вы можете добавить или удалить слово, '
                          f'а также посмотреть статистику обучения', 
                          reply_markup=markup_pref)


@bot.message_handler(func=lambda message: message.text == 'Назад в меню')
def back_menu(message):
    """Выход из функций добавления, удаления слов/ статистики в раздел настроек"""
    preferences(message)


@bot.message_handler(func=lambda message: message.text == 'Следующее слово')
def next_word_cicle(message):
    """Функция создает новые карточки в процессе обучения"""
    education(message)


@bot.message_handler(func=lambda message: user_step[message.chat.id] == 'education')
def check_word(message):
    """Функция проверки слов. Если перевод угаданного слова верен, то счетчик изученности ("progress_study") увеличивается на 1
    Если слово из общего словаря отсутствует в пользовательском словаре, то оно добавляется в словарь пользователя.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        target_word_trans = data['target_word_trans']
        if message.text == target_word_trans:
            bot.send_message(message.chat.id, text=f'Верно!\n{target_word_trans} - {target_word}')
            if db_bot.check_word(message.from_user.id, message.text) is True:
                db_bot.make_progress_study(message.from_user.id, target_word)
            else:
                db_bot.add_word(message.from_user.id, target_word, target_word_trans, 
                                get_example(target_word_trans))
        else:
            bot.send_message(message.chat.id, text=f'Неверно! Попробуйте другой вариант ответа')

 
@bot.message_handler(func=lambda message: message.text == 'Добавить слово')
def add_word_greet(message):
    """Приветственное сообщение при добавлении слова"""
    bot.set_state(message.from_user.id, MyStates.add_word, message.chat.id)
    user_step[message.chat.id] = 'add_word'
    markup_addition = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_menu_btn = types.KeyboardButton('Назад в меню')
    markup_addition.add(back_menu_btn)
    bot.send_message(message.chat.id, text='Введите слово, которое хотите добавить', 
                     reply_markup=markup_addition)
    return message.text


@bot.message_handler(func=lambda message: user_step[message.chat.id] == 'add_word')
def add_word(message):
    """Функция добавления слова"""
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['add_word'] = message.text
        if db_bot.check_word(message.from_user.id, translate_word(message.text).lower()) is True:
            bot.send_message(message.chat.id, text='Данное слово уже есть в словаре, укажите другое')
        else:
            db_bot.add_word(message.from_user.id, message.text.lower(), translate_word(message.text), 
                            get_example(translate_word(message.text)))
            bot.send_message(message.chat.id, text=f'Добавлено новое слово: {message.text.lower()}, '
                                                   f'перевод: {translate_word(message.text)}. '
                                                   f'Количество слов в словаре: '
                                                   f'{db_bot.count_user_words(message.from_user.id)}')


@bot.message_handler(func=lambda message: message.text == 'Удалить слово')
def del_word_greet(message):
    """Приветственное сообщение при удалении слова"""
    user_step[message.chat.id] = 'del_word'
    bot.set_state(message.from_user.id, MyStates.del_word, message.chat.id)
    markup_deletion = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_menu_btn = types.KeyboardButton('Назад в меню')
    markup_deletion.add(back_menu_btn)
    bot.send_message(message.chat.id, text='Введите слово, которое хотите удалить', reply_markup=markup_deletion)
    return message.text


@bot.message_handler(func=lambda message: user_step[message.chat.id] == 'del_word')
def del_word(message):
    """Функция удаления слова"""
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['del_word'] = message.text
        if db_bot.check_word(message.from_user.id, translate_word(message.text).lower()) is False:
            bot.send_message(message.chat.id, text='Данное слово отсутствует в словаре, укажите другое')
        else:
            db_bot.del_word(message.from_user.id, message.text.lower())
            bot.send_message(message.chat.id, text=f'Слово: {message.text.lower()} удалено. '
                                                    f'Количество слов в словаре: '
                                                    f'{db_bot.count_user_words(message.from_user.id)}')


@bot.message_handler(func=lambda message: message.text == 'Статистика')
def get_stat(message):
    """Функция вывода статистики. Выводит количество слов в словаре пользователя (с учетом автоматического добавления из общего словаря),
    Количество изученных слов (количество верных угадываний не меньге 5) и последнее добавленное слово.
    """
    markup_stat = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_menu_btn = types.KeyboardButton('Назад в меню')
    markup_stat.add(back_menu_btn)
    bot.send_message(message.chat.id, text=f'Ваша статистика:\n\n'
                                           f'Слов в Вашем словаре: '
                                           f'{db_bot.count_user_words(message.from_user.id)}. \n'
                                           f'Изучено слов (количество верных угадываний 5 и более): '
                                           f'{db_bot.count_fin_user_words(message.from_user.id)}. \n'
                                           f'Последнее добавленное слово: '
                                           f'{db_bot.get_last_add_word(message.from_user.id)[0]}, '
                                           f'перевод: {db_bot.get_last_add_word(message.from_user.id)[1]}', 
                                           reply_markup=markup_stat)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
