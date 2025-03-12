export LANGUAGE=ru_RU.UTF-8
export LC_ALL="ru_RU.UTF-8"
export LC_CTYPE="ru_RU.UTF-8"
gunicorn --bind 0.0.0.0:8080 foodgram.wsgi