def format_shopping_list(cart, recipes):
    ingredients_info = [
        '{}. {} - {} ({})'.format(
            index,
            ingredient['ingredient_name'].capitalize(),
            ingredient['total_amount'],
            ingredient['ingredient_unit']
        )
        for index, ingredient in enumerate(cart, start=1)
    ]

    shopping_list = '\n'.join([
        'Список ингредиентов:',
        *ingredients_info,
        'Список рецептов:',
        *[f'• {recipe}' for recipe in recipes]
    ])
    return shopping_list
