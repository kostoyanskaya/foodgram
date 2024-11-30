import json
import os

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    help = 'Import data from JSON file'

    def import_data(self, model_class, json_file_name, additional_fields=None):
        json_file_path = os.path.join('data', json_file_name)

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            objects = [
                model_class(**{**item, **additional_fields(item)})
                for item in data
            ] if additional_fields else [
                model_class(**item) for item in data
            ]

            model_class.objects.bulk_create(objects, ignore_conflicts=True)

        return len(objects)
