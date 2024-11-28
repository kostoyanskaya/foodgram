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
            ingredients = (
                Ingredient(
                    name=row[0].strip(),
                    measurement_unit=row[1].strip()
                )
                for row in reader
            )

            Ingredient.objects.bulk_create(ingredients)

        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно импортированы')
        )
