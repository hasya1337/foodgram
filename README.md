![example workflow](https://github.com/hasya1337/foodgram/actions/workflows/main.yml/badge.svg)

## Описание проекта
Foodgram - проект социальной сети с возможностью публикации рецептов блюд, добавления их в избранное, корзину и формирования списка покупок.

Проект доступен по адресу https://foodgramsmirnov.hopto.org

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

## Стек
- python
- Django
- DRF
- Nginx
- Docker

## Как развернуть проект
На машине, в которой будет развернут проект, необходимы установленные Git и Docker.

1. Копируем проект на машину
```bash 
git clone https://github.com/hasya1337/foodgram.git
```
2. Переходим в директорию проекта
```bash
cd foodgram
```
3. Создаем файл с переменными окружения .env
Он должен содержать следующие переменные:
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DB_HOST
DB_PORT
SECRET_KEY
ALLOWED_HOSTS
DEBUG
DB_POSTGRE
4. Для сборки из текущего репозитория выполняем:
```bash
docker compose up -d
```
Для сборки из Docker Hub выполняем:
```bash
docker compose -f docker-compose.production.yml up -d
```
Осуществляем миграции:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
Собираем статику:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/static/
```
Заполняем таблицы Ingredient и Tag через файлы csv
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loadingredients
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loadtags
```
или файлы json
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loadingredientsjson
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loadtagsjson
```
## Доступ к документации API
Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.
## Развертывание без Docker
1. Копируем проект на машину
```bash 
git clone https://github.com/hasya1337/foodgram.git
```
2. Переходим в директорию проекта
```bash
cd foodgram
```
3. Создаем и активируем виртуальное окружение
Windows 

```
python -m venv venv
``` 
```
source venv/Scripts/activate
``` 

Linux/macOS

```
python3 -m venv venv
``` 
```
source venv/bin/activate
```
4. Устанавливаем зависимости
``` 
pip install -r backend/requirements.txt
``` 
5. Создаем файл с переменными окружения .env
Он должен содержать следующие переменные:
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DB_HOST
DB_PORT
SECRET_KEY
ALLOWED_HOSTS
DEBUG
DB_POSTGRE
6. В папке backend осуществляем миграции
```
python manage.py migrate
```
7. Заполняем таблицы Ingredient и Tag через файлы csv
```
python manage.py loadingredients
python manage.py loadtags
```
или файлы json
```
python manage.py loadingredientsjson
python manage.py loadtagsjson
```
8. Запускаем проект
```
python manage.py runserver
```

Автор [Хасянов Тимур](https://github.com/hasya1337)