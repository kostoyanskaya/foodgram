from .import_base import BaseImportCommand
from recipes.models import Ingredient


class Command(BaseImportCommand):
    help = 'Import ingredients from CSV file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(
            Ingredient, 'ingredients.csv', ['name', 'measurement_unit']
        )
        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты успешно импортированы: {created_count}'
        ))
