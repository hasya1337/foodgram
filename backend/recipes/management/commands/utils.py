import json


class JsonLoadCommand:

    def handle(self):
        with open(self.file, 'r', encoding='utf-8') as file:
            items_created = self.model.objects.bulk_create(
                (self.model(**tag) for tag in json.load(file)),
                ignore_conflicts=True)
            self.stdout.write(f'Загружено {len(items_created)} тегов')
