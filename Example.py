"""
Модуль Example отвечает за поиск значения слова в dictionaryapi

----

В модуле импортированы: request, pprint

"""
import requests
from pprint import pprint


url = 'https://api.dictionaryapi.dev/api/v2/entries/en/'

def get_example(word):
    """Функция получения примера использования слова из сервиса dictionaryapi. Функция недоработана!
    Из-за пострения ответов от сервиса блоки 'example' находятся в разных частях ответа и их надо вылавливать"""
    word_example = requests.get(f'{url}{word}').json()[0]['meanings']
    examples_list = []
    for i in range(len(word_example)):
        for j in word_example[i]['definitions']:
            if 'example' in j.keys():
                examples_list.append(j['example'])
    try:
        return examples_list[0]
    except IndexError:
        return None


if __name__ == '__main__':
    print(get_example('cat'))
