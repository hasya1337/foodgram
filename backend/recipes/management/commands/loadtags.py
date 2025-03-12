from csv import reader

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        with open('data/tags.csv', 'r', encoding='utf-8') as tag_file:
            tags = Tag.objects.bulk_create(
                (Tag(name=row[0], slug=row[1]) for row in reader(tag_file)),
                ignore_conflicts=True)
            self.stdout.write(f'Загружено {len(tags)} тегов')
