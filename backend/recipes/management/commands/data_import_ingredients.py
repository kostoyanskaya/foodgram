import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


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
                    'measurement_unit': item['measurement_unit'],
                }
                objects.append(model_class(**obj_data))
            model_class.objects.bulk_create(objects, ignore_conflicts=True)

        return len(objects)


class Command(BaseImportCommand):
    help = 'Import ingredients from JSON file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(Ingredient, 'ingredients.json')
        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты успешно импортированы: {created_count}'
        ))
