from django.core.management.base import BaseCommand

from recipes.models import Ingredient

from .utils import JsonLoadCommand


class Command(JsonLoadCommand, BaseCommand):
    help = 'Начало загрузки файлов'
    model = Ingredient
    file = 'data/ingredients.json'
