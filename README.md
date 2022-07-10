# yatube_project
## Описание

Социальная сеть для публикации личных дневников. В ней ты можешь:
 - Cоздать свою страницу
 - Публиковать записи
 - Вступать в сообщества
 - Подписываться на других авторов и комментировать их посты

## Запуск проекта в dev-режиме

1. Установите и активируйте виртуальное окружение
```python
python3 -m venv venv
```
2. Установите зависимости из файла requirements.txt
```python
pip install -r requirements.txt
```
3. Примените миграции:
```python
python3 manage.py migrate
```
4. Чтобы запустить работу сайта, в папке с файлом manage.py выполните команду:
```python
python3 manage.py runserver
```
5. Чтобы запустить тесты, в папке с файлом manage.py выполните команду:
```python
python3 manage.py test
```
6. Чтобы создать суперпользователя, в папке с файлом manage.py выполните команду:
```python
python3 manage.py createsuperuser
```

## Технологии
- Python 3.7
- Django 2.2.19

### Автор

_Рябов В.С._
_email: ryabov.v.s@yandex.ru_
_github: https://github.com/bigbang13_
