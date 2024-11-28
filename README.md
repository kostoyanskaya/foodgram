#  Проект: Foodgram
«Фудграм» — это веб-сайт, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок», который позволяет создавать список продуктов, необходимых для приготовления выбранных блюд. «Фудграм» создаёт удобное пространство для обмена рецептами и планирования покупок, делая процесс приготовления пищи более структурированным и приятным.
# Ссылка на проект: 
#### [_https://foodgramdelicious.ddnsking.com_](https://foodgramdelicious.ddnsking.com)
### Основные возможности:
- Пользователи могут публиковать свои рецепты.
- Возможность добавления чужих рецептов в избранное.
- Подписка на публикации других авторов.
- Сервис «Список покупок» для создания списка необходимых продуктов.
- Автоматическая переадресация на страницу входа после регистрации.
- Возможность получения уникальной короткой ссылки на рецепт.
- Залогиненные пользователи могут добавлять рецепты в избранное и список покупок.
- Пользователи могут скачивать свой список покупок в формате .txt.
- Редактирование опубликованных рецептов для их авторов.


### В проекте используются  основные следующие технологии и библиотеки:

- Django - основной фреймворк для разработки веб-приложений.
- Django REST Framework - для построения API.
- Djoser - для управления аутентификацией и регистрацией пользователей.
- Pillow - библиотека для обработки изображений.
- PostgreSQL - в качестве базы данных.
- Gunicorn - WSGI HTTP сервер для запуска приложения.

## Установка проекта на удаленном сервере:

1. Выполнить вход на удаленный сервер.

2. Выполните на сервере команды для установки Docker и Docker Compose для Linux

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```

3. Создайте папку foodgram

```
sudo mkdir foodgram
```

4. Переход в директорию foodgram

```
cd foodgram/
```

5. Нужно создать фаил docker-compose.production.yml и скопировать  содержимое 
docker-compose.production.yml проекта

```
sudo touch docker-compose.production.yml
sudo nano docker-compose.production.yml
```

6. Нужно создать фаил .env

```
sudo touch .env
sudo nano .env
```
7. Заполнить по примеру

```
POSTGRES_DB=example
POSTGRES_USER=example_user
POSTGRES_PASSWORD=example_password
DB_NAME=example
DB_HOST=db
DB_PORT=5432
```

8. Добавить домен сайта в файл конфигурации Nginx и проверить конфигурацию, выполнить перезагрузку.
```
sudo nano /etc/nginx/sites-enabled/default
sudo nginx -t
sudo service nginx reload
```

9. Выполнить команды:

```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/backend_static/static/. /backend_static/static/
```
10. Загрузить ингредиенты:

```
docker exec -it <имя_контейнера> bash
python manage.py import_ingredients
python manage.py import_tags
```

## Автор
#### [_Анастасия_](https://github.com/kostoyanskaya/)