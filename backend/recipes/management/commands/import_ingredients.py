import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from CSV file'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join('data', 'ingredients.csv')

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                name = row[0].strip()
                measurement_unit = row[1].strip()
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )

        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно импортированы')
        )
