from rest_framework import serializers


def validate_ingredients(ingredients):
    if not ingredients:
        raise serializers.ValidationError(
            'Поле ingredients не должно быть пустым.'
        )

    ingredient_ids = []
    for ingredient in ingredients:
        if ingredient['amount'] < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )
        if ingredient['id'] in ingredient_ids:
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        ingredient_ids.append(ingredient['id'])

    return ingredients


def validate_tags(tags):
    if not tags:
        raise serializers.ValidationError('Поле tags не должно быть пустым.')

    if len(tags) != len(set(tags)):
        raise serializers.ValidationError('Теги не должны повторяться.')

    return tags
