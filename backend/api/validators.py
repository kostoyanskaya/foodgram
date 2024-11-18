from rest_framework import serializers


def validate_tags(value):
    if not value:
        raise serializers.ValidationError("Поле tags не должно быть пустым.")
    if len(value) != len(set(value)):
        raise serializers.ValidationError("Теги не должны повторяться.")
    return value


def validate_ingredients(self, value):
    if not value or (isinstance(value, list) and len(value) == 0):
        raise serializers.ValidationError("Ингредиент не выбран.")

    ingredient_ids = []
    for ingredient in value:
        if ingredient['amount'] < 1:
            raise serializers.ValidationError(
                "Количество ингредиента должно быть больше 0"
            )
        ingredient_ids.append(ingredient['ingredient']['id'])

    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError("Ингредиенты не должны повторяться.")

    return value
