from rest_framework import serializers


def validate_tags(value):
    if not value:
        raise serializers.ValidationError("Поле tags не должно быть пустым.")
    if len(value) != len(set(value)):
        raise serializers.ValidationError("Теги не должны повторяться.")
    return value
