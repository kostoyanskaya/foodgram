def format_shopping_list(ingredients_info, recipes):
    shopping_list = '\n'.join([
        'Список ингредиентов:',
        *ingredients_info,
        'Список рецептов:',
        *[f'• {recipe}' for recipe in recipes]
    ])
    return shopping_list
