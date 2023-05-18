"""
Модуль db_bot отвечает за создание базы данных, её наполнение и манупуляцию с данными.

----

1.Раздел создания (удаления) БД
drope_db - удаление БД
create_db - создание БД

----

2.Раздел манипуляции с данными:
2.1. Работа с таблицей пользователей:
add_user - добавление нового пользователя.
check_user - проверка существование пользователя в БД.
2.2. Работа с одщим словарем:
add_word_gd - заполение общего словаря заранее отобранным набором слов. Данная функция не участвует в работе телеграмм-бота.
get_words_gd - выборка слов из общего словаря. Используется для создания "карточек" в телеграмм-боте.
2.3. Работа с тадлицей пользовательского словаря
add_word - добавление слова в словарь пользователя
check_word - проверка существования слова в словаре. Необходимо для:
    - исключения дублирования слов при добавлении, 
    - исключения ошибок программы при удалении слов,
    - проверки правильного выбора слова при обучении.
get_words - выборка слов из словаря пользователя.
get_study_words - выборка изучаемых слов (количество правильных угадываний слова меньше 5).
del_word - удаление слова.
count_user_words - подсчет слов в словаре пользователя.
count_fin_user_words - подсчет изученных слов в словаре пользователя (количество правильных угадываний слова не меньше 5).
make_progress_study - повышение ранга изученности слова на 1.
get_last_add_word - показывает последнее добавленно в словарь слово.

----

В модуле импортированы: psycopg2, config

"""

import psycopg2
import config
from Example import *

conn = psycopg2.connect(database="Telebot_Dict", user="postgres", password=config.db_password)

## Функции удаления, создания базы данных
# Функция удаления базы данных
def drope_db(conn=conn, cursor=conn.cursor()):
    cursor.execute("""
    DROP TABLE IF EXISTS general_dict;
    DROP TABLE IF EXISTS bot_user, user_dict CASCADE;
    """)
    conn.commit()
    return 'База данных удалена'

## Функции создания (удаления) базы данных
def create_db(conn=conn, cursor=conn.cursor()):
    cursor.execute("""
    DROP TABLE IF EXISTS general_dict;
    DROP TABLE IF EXISTS bot_user, user_dict CASCADE;
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_user(
        id SERIAL PRIMARY KEY,
        bot_uid INTEGER UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS general_dict(
        id SERIAL PRIMARY KEY,
        ru_word VARCHAR(30) NOT NULL,
        en_word VARCHAR(30) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_dict(
        id SERIAL PRIMARY KEY,
        ru_word_user VARCHAR(30) NOT NULL,
        en_word_user VARCHAR(30) NOT NULL,
        example VARCHAR(150),
        progress_study INTEGER,
        bot_uid INTEGER NOT NULL REFERENCES bot_user(bot_uid) ON DELETE CASCADE
    );
    """)
    conn.commit()
    return 

## Функции манипуляции с данными в базе данных
# Работа с таблицей пользователей (bot_user)
def add_user(user_id, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute(""" 
        INSERT INTO bot_user(id, bot_uid) VALUES(default, %s)
        ON CONFLICT(bot_uid)
        DO NOTHING;
        """, (user_id, ))
        conn.commit()
        return f'Пользователь {user_id} добавлен'

def check_user(user_id, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute(""" 
        SELECT EXISTS(SELECT 1 FROM bot_user WHERE bot_uid=%s limit 1)
        """, (user_id, ))
        conn.commit()
        return cursor.fetchone()[0]

# Работа с таблицей общего словаря (general_dict)
def add_word_gd(ru_word, en_word, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO general_dict(ru_word, en_word) 
        VALUES(%s, %s)
        """, (ru_word, en_word))
        conn.commit()

def get_words_gd(conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT ru_word, en_word FROM general_dict
        """)
        conn.commit()
        return cursor.fetchall()

# Работа с таблицей пользовательского словаря (user_dict)
def add_word(user_id, ru_word, en_word, example, progress=0, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO user_dict(id, ru_word_user, en_word_user, example, progress_study, bot_uid) 
                       VALUES(default, %s, %s, %s, %s, %s)
        """, (ru_word, en_word, example, progress, user_id))
        conn.commit()
        return ru_word

def check_word(user_id, en_word, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT EXISTS(SELECT 1 FROM user_dict WHERE bot_uid=%s and en_word_user=%s)
        """, (user_id, en_word))
        conn.commit()
        return cursor.fetchone()[0]

def get_words(user_id, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT ru_word_user, en_word_user FROM user_dict
        WHERE bot_uid=%s
        """, (user_id, ))
        conn.commit()
        return cursor.fetchall()

def get_study_words(user_id, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT ru_word_user, en_word_user FROM user_dict
        WHERE bot_uid=%s
        AND progress_study < 5
        """, (user_id, ))
        conn.commit()
        return cursor.fetchall()

def del_word(user_id, ru_word, conn=conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        DELETE FROM user_dict 
         WHERE bot_uid=%s 
           AND ru_word_user=%s
        RETURNING ru_word_user
        """, (user_id, ru_word))
        conn.commit()
        return cursor.fetchone()[0]

def count_user_words(user_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT COUNT(ru_word_user) 
          FROM user_dict 
         WHERE bot_uid=%s
        """, (user_id, ))
        conn.commit()
        return cursor.fetchone()[0]

def count_fin_user_words(user_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT COUNT(ru_word_user) 
          FROM user_dict 
         WHERE bot_uid=%s 
           AND progress_study >= 5
        """, (user_id, ))
        conn.commit()
        return cursor.fetchone()[0]

def make_progress_study(user_id, ru_word):
    with conn.cursor() as cursor:
        cursor.execute("""
        UPDATE user_dict 
           SET progress_study = progress_study + 1 
         WHERE bot_uid=%s 
           AND ru_word_user=%s
        """, (user_id, ru_word))
        conn.commit() 

def get_last_add_word(user_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT ru_word_user, en_word_user
          FROM user_dict 
         WHERE id = 
            (SELECT MAX(id) 
               FROM user_dict
              WHERE bot_uid=%s)
        """, (user_id, ))
        conn.commit()
        return cursor.fetchone()



if __name__ == '__main__':
    general_dict = {'мир': ['world', 'Пример использования', 0],
                'время': ['time', 'Пример использования', 0],
                'кот': ['cat', 'Пример использования', 0],
                'животное': ['animal', 'Пример использования', 0],
                'дом': ['house', 'Пример использования', 0],
                'город': ['city', 'Пример использования', 0],
                'автомобиль': ['car', 'Пример использования', 0],
                'он': ['he', 'Пример использования', 0],
                'она': ['she', 'Пример использования', 0],
                'мы': ['we', 'Пример использования', 0],
                }
    # for v in general_dict.values():
    #     print(Example.get_example(v[0]))
    # print(__doc__)
    # print(create_db())
    # for k, v in general_dict.items():
    #     add_word_gd(k, v[0])
    # print(add_user(405323796))
    # print(check_user(405323796))
    # print(check_word(405323796, 'animal'))
    # print(del_word(405323796, 'нос'))
    # print(count_user_words(405323796))
    # print(count_fin_user_words(405323796))
    # print(make_progress_study(405323796, 'кот'))
    # print(get_last_add_word(405323796))
    # print(get_words_gd())
    # print(get_words(405323796))


