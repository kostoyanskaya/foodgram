import json
import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from recipes.models import Tag


class BaseImportCommand(BaseCommand):
    help = 'Import data from JSON file'

    def import_data(self, model_class, json_file_name):
        json_file_path = os.path.join('data', json_file_name)

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            objects = []
            for item in data:
                obj_data = {
                    'name': item['name'],
                    'slug': item.get('slug') or slugify(item['name']),
                }
                objects.append(model_class(**obj_data))
            model_class.objects.bulk_create(objects, ignore_conflicts=True)

        return len(objects)


class Command(BaseImportCommand):
    help = 'Import tags from JSON file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(Tag, 'tags.json')
        self.stdout.write(self.style.SUCCESS(
            f'Теги успешно импортированы: {created_count}'
        ))
