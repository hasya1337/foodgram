from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe


def decode_link(request, id):
    if not Recipe.objects.filter(id=id).exists():
        raise ValidationError(
            f'Рецепта с id {id} не существует!'
        )
    return redirect(f'/recipes/{id}')
