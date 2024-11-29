from .import_base import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    help = 'Import tags from CSV file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(
            Tag, 'tags.csv', ['name', 'slug']
        )
        self.stdout.write(
            self.style.SUCCESS(f'Теги успешно импортированы: {created_count}')
        )
