from csv import reader

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        with open(
            'data/ingredients.csv',
            'r',
            encoding='utf-8'
        ) as ingredient_file:
            ingredients = Ingredient.objects.bulk_create(
                (Ingredient(
                    name=row[0], measurement_unit=row[1]
                ) for row in reader(ingredient_file)),
                ignore_conflicts=True
            )
            self.stdout.write(f'Загружено {len(ingredients)} продуктов')
