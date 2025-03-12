from datetime import datetime as dt

DELIMETER = '\n'

REPORT_NAME = 'Список покупок'

INGREDIENTS_LIST = 'Список продуктов'

RECIPES_LIST = 'Список рецептов'

TEMPLATE_INGREDIENTS = '{}. {} {} {}.'

TEMPLATE_RECIPES = '{}. {}'

MAX_MEASURE_VISUAL = 2

# на докер образ не получилось установить локали, поэтому реализую
# дату таким образом
MONTHS = [
    'января', 'февраля', 'марта',
    'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября',
    'октября', 'ноября', 'декабря'
]


def form_shopping_cart(recipes_names, ingredients):
    date = f'{dt.now().day} {MONTHS[int(dt.now().month) - 1]} {dt.now().year}'
    # date = dt.today().strftime('%d %B %Y')
    ingredients_to_text = DELIMETER.join([
        TEMPLATE_INGREDIENTS.format(
            number,
            ingredient['ingredient__name'].capitalize(),
            ingredient['amount'],
            ingredient['ingredient__measurement_unit'][:MAX_MEASURE_VISUAL]
        ) for number, ingredient in enumerate(ingredients, 1)
    ])
    recipes_to_text = DELIMETER.join(
        (TEMPLATE_RECIPES.format(
            number, name
        ) for number, name in enumerate(recipes_names, 1))
    )
    return DELIMETER.join([
        date,
        REPORT_NAME,
        INGREDIENTS_LIST,
        ingredients_to_text,
        RECIPES_LIST,
        recipes_to_text
    ])
