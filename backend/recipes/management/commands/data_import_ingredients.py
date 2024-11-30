from .data_import_base import BaseImportCommand
from recipes.models import Ingredient


class IngredientImportCommand(BaseImportCommand):
    help = 'Import ingredients from JSON file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(Ingredient, 'ingredients.json')
        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты успешно импортированы: {created_count}'
        ))
