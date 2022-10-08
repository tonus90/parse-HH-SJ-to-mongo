from pymongo import MongoClient
from pprint import pprint

"""
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные вакансии в созданную БД.
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы.
3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.
"""
salary = 200000

client = MongoClient('localhost', 27017)
db = client['vacancies']
vacancies = db['vacancies_hh']
vacancies_sj = db['vacancies_sj']

res1 = vacancies.find({'$or': [{'min_sal': {'$gte': salary}}, {'max_sal': {'$gte': salary}}]}) #второе задание
res2 = vacancies_sj.find({'$or': [{'min_sal': {'$gte': salary}}, {'max_sal': {'$gte': salary}}]})


def vprint(res): #функция для вывода
    for vacs in res:
        pprint(vacs)

vprint(res1)
vprint(res2)


