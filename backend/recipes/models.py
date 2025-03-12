from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (
    MAX_LENGHT, MAX_USER_LENGHT, MAX_LENGHT_EMAIL, MINIMAL_AMOUNT, MINIMAL_TIME
)


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=MAX_LENGHT_EMAIL
    )
    avatar = models.ImageField(
        upload_to='users/', null=True,
        blank=True, verbose_name='Аватар пользователя'
    )
    username = models.CharField(
        verbose_name='Логин', max_length=MAX_USER_LENGHT, unique=True,
        validators=[
            RegexValidator(regex=r'[^\w.@+-]', inverse_match=True)
        ]
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=MAX_USER_LENGHT
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=MAX_USER_LENGHT
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGHT, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_ingredients'
        ),)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Название',
        unique=True
    )
    slug = models.SlugField(
        max_length=MAX_LENGHT,
        unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Продукты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    name = models.CharField(max_length=MAX_LENGHT, verbose_name='Название')
    text = models.TextField('Описание')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        auto_now=True
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(MINIMAL_TIME)
        ],
        default=MINIMAL_TIME,
        verbose_name='Время (мин)'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MINIMAL_AMOUNT)], default=MINIMAL_AMOUNT,
        verbose_name='Мера'
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        constraints = (models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipeingredients'
        ),)

    def __str__(self):
        return f'{self.ingredient.name}, {self.ingredient.measurement_unit}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)ss'
            ),
        )
        ordering = ('user',)

    def __str__(self):
        return f'{self.user.username} добавил к себе {self.recipe.name}'


class Favorite(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShopingCart(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'


class Subscription(models.Model):
    follower = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='followers',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='authors',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'author'),
                name='unique_subscription'
            ),
        )

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'
