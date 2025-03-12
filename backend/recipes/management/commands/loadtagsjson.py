from django.core.management.base import BaseCommand

from recipes.models import Tag

from .utils import JsonLoadCommand


class Command(JsonLoadCommand, BaseCommand):
    help = 'Начало загрузки файлов'
    model = Tag
    file = 'data/tags.json'
