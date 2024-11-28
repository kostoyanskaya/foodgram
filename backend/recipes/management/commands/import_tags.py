import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Import tags from CSV file'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join('data', 'tags.csv')

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            tags = (
                Tag(
                    name=row[0].strip(),
                    slug=row[1].strip()
                )
                for row in reader
            )

            Tag.objects.bulk_create(tags)

        self.stdout.write(self.style.SUCCESS(
            'Теги успешно импортированы')
        )
