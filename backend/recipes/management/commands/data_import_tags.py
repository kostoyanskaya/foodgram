from django.utils.text import slugify

from .data_import_base import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    help = 'Import tags from JSON file'

    def handle(self, *args, **kwargs):
        created_count = self.import_data(
            Tag, 'tags.json', additional_fields=self.tag_additional_fields
        )
        self.stdout.write(self.style.SUCCESS(
            f'Теги успешно импортированы: {created_count}'
        ))

    def tag_additional_fields(self, item):
        return {'slug': item.get('slug') or slugify(item['name'])}
