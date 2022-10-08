"""
Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы) с сайтов Superjob и HH. Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы). Получившийся список должен содержать в себе минимум:
* Наименование вакансии.
* Предлагаемую зарплату (отдельно минимальную, максимальную и валюту).
* Ссылку на саму вакансию.
* Сайт, откуда собрана вакансия.
"""
"""
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные вакансии в созданную БД.
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы.
3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.
"""

from bs4 import BeautifulSoup
import requests
from pathlib import Path
import json
from time import sleep
from urllib.parse import urljoin
from pymongo import MongoClient

class JobParse:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'}
    base_url = 'https://hh.ru'

    def __init__(self, start_url: str, client):
        self.start_url = start_url
        self.client = client
        self.db = self.client['vacancies']
        self.collections = self.db['vacancies_hh']

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            sleep(2)

    def _get_soup(self, url):
        response = self._get_response(url)
        return BeautifulSoup(response.text, 'html.parser')

    def _parse(self, vacancy):
        data = {}
        for key, funk in self._get_template().items():
            try:
                data[key] = funk(vacancy)
            except AttributeError:
                pass
        return data

    def _save(self, data:dict): #Сохраняем только новые записи
        try:
            if self.collections.count_documents({'url': data['url']}) > 0:
                pass
            else: self.collections.insert_one(data)
        except KeyError as err:
            self.collections.insert_one(data)
            print(err)

    def run(self):
        url = self.start_url
        cnt = 0
        cnt_pages = 0
        while url:
            soup = self._get_soup(url)
            get = soup.find('a', attrs={'class': 'bloko-button HH-Pager-Controls-Next HH-Pager-Control'})
            try:
                url = urljoin(self.base_url, get.attrs.get('href', ''))
            except AttributeError as err:
                print(err)
                url = False
            catalog_vac = soup.find('div', attrs={'class': "vacancy-serp"})
            for vac in catalog_vac.find_all('div', attrs={'class': "vacancy-serp-item"}):
                vacancies_data = self._parse(vac)
                cnt += 1
                self._save(vacancies_data)
            cnt_pages += 1
            print(cnt_pages)
            print(cnt)

    def _get_template(self):
        return {
            'name': lambda vac: vac.find('a', attrs={'class': "bloko-link HH-LinkModifier HH-VacancyActivityAnalytics-Vacancy"}).text,
            'url': lambda vac: vac.find('a', attrs={'class': "bloko-link HH-LinkModifier HH-VacancyActivityAnalytics-Vacancy"}).attrs.get('href', ''),
            'min_sal': lambda vac: self._get_salary(vac.find('div', attrs={'class': 'vacancy-serp-item__sidebar'}))[0], #теперь один метод для зп
            'max_sal': lambda vac: self._get_salary(vac.find('div', attrs={'class': 'vacancy-serp-item__sidebar'}))[1],
            'valuta': self._get_valuta,
        }

    def _get_salary(self, work):
        try:
            sal = work.find('span', attrs={'class': 'bloko-section-header-3 bloko-section-header-3_lite'}).text
        except Exception as err:
            print(err)
            min_s = None
            max_s = None
            return (min_s, max_s) #кортеж нон тайпов если нет вообще зп
        print(sal)
        use = (sal.replace(u'\xa0', ''))
        print(use)

        my_list = use.split()
        if my_list[0].find('-') != -1:
            min_s = float(f'{my_list[0].split("-")[0]}')
            max_s = float(f'{my_list[0].split("-")[1]}')
        elif my_list[0] == 'от':
            min_s = float(f'{my_list[1]}')
            max_s = None
        elif my_list[0] == 'до':
            min_s = None
            max_s = float(f'{my_list[1]}')
        else:
            min_s = None
            max_s = None
        return (min_s, max_s)

    def _get_valuta(self, vac):
        work = vac.find('div', attrs={'class': 'vacancy-serp-item__sidebar'})
        try:
            sal = work.find('span', attrs={'class': 'bloko-section-header-3 bloko-section-header-3_lite'}).text
        except Exception as err:
            print(err)
            return None
        print(sal)
        use = (sal.replace(u'\xa0', ''))
        print(use)
        my_list = use.split()
        if my_list[0].find('-') != -1:
            val = my_list[1]
        elif my_list[0] == 'от' or my_list[0] == 'до':
            if len(my_list) == 4:
                val = f'{my_list[2]} {my_list[3]}'
            else:
                val = my_list[2]
        else:
            val = None
        return val


if __name__ == '__main__':
    name = input('Введите должность: ')
    url = f'https://hh.ru/search/vacancy?L_is_autosearch=false&clusters=true&enable_snippets=true&text={name}&page=0'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'}

    client = MongoClient('localhost', 27017)

    parser = JobParse(url, client)
    try:
        parser.run()
    except ValueError as err:
        print(err)
        pass
