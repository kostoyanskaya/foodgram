import os
import csv
from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    help = 'Import data from CSV file'

    def import_data(self, model_class, csv_file_name, fields):
        csv_file_path = os.path.join('data', csv_file_name)

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            objects = []
            for row in reader:
                obj_data = {field: row[i].strip() for i, field in enumerate(
                    fields
                )}
                objects.append(model_class(**obj_data))
            model_class.objects.bulk_create(objects, ignore_conflicts=True)

        return len(objects)
