"""
Модуль YandexDict отвечает за поиск слова в словаре Яндекса, используя Dictionary API

----

В модуле импортированы: request, pprint, config

"""

import requests
from pprint import pprint
from config import *


url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'


def translate_word(word, token=token_dict, from_lang_tr='ru', to_lang_tr='en'):
    param = {'key': token,
             'lang': f'{from_lang_tr}-{to_lang_tr}',
             'text': word,
             'ui': 'ru'}
    trans_word = requests.get(url=url, params=param).json()
    return trans_word['def'][0]['tr'][0]['text']


if __name__ == '__main__':
    word = 'старт'
    pprint(translate_word(word))
