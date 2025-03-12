from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShopingCart,
                            Subscription, Tag)


User = get_user_model()

admin.site.unregister(Group)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'
    MIDDLE_BORDER = 5
    LONG_BORDER = 30
    QUERYSET_VALUES = dict(
        quick=(0, MIDDLE_BORDER),
        middle=(MIDDLE_BORDER + 1, LONG_BORDER),
        long=(LONG_BORDER + 1, 10**10)
    )

    def lookups(self, request, model_admin):
        count_list = [
            model_admin.get_queryset(request).filter(
                cooking_time__range=value
            ).count() for value in self.QUERYSET_VALUES.values()
        ]
        return (
            ('quick',
             f'Быстрее {self.MIDDLE_BORDER+1} мин. ({count_list[0]})'),
            ('middle', f'Быстрее {self.LONG_BORDER+1} мин. ({count_list[1]})'),
            ('long', f'{self.LONG_BORDER+1} мин. и дольше ({count_list[2]})')
        )

    def queryset(self, request, queryset):
        if self.value() in self.QUERYSET_VALUES:
            return queryset.filter(
                cooking_time__range=self.QUERYSET_VALUES.get(self.value())
            )
        return queryset


class RecipeCountMixin():

    @admin.display(description='Рецепты')
    def recipe_count(self, model):
        return model.recipes.count()


@admin.register(Ingredient)
class IngridientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    list_filter = ('measurement_unit', )
    search_fields = ('name', 'measurement_unit',)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    fk_name = 'recipe'
    extra = 0
    verbose_name = 'Продукт'
    verbose_name_plural = 'Продукты'


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug', )


@admin.register(Favorite, ShopingCart)
class FavoriteAndCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'author')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorite_count', 'tags_override',
                    'ingredients_override', 'cooking_time', 'image_override')
    search_fields = (
        'name', 'author__first_name',
        'author__last_name', 'author__username', 'tags__name'
    )
    list_filter = ['tags', 'author', CookingTimeFilter]
    readonly_fields = ('image_override',)
    inlines = (IngredientsInLine, )

    @admin.display(description='Избранное')
    def favorite_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Теги')
    @mark_safe
    def tags_override(self, recipe):
        return '<br>'.join(recipe.tags.values_list('name', flat=True))

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_override(self, recipe):
        return '<br>'.join([
            '{ingredient__name} {ingredient__measurement_unit} {amount}'
            .format(
                **ingredient
            ) for ingredient in recipe.recipe_ingredients.values(
                'ingredient__name', 'ingredient__measurement_unit', 'amount'
            )
        ])

    @admin.display(description='Изображение')
    def image_override(self, recipe):
        return mark_safe(
            f'<img src="{recipe.image.url}" width="100" height="100"/>'
        )


class UserSimpleListFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return self.VALUES

    def queryset(self, request, queryset):
        if self.value() in self.QUERYSET_VALUES:
            return queryset.distinct().filter(
                **self.QUERYSET_VALUES.get(self.value())
            )
        return queryset


class FollowersFilter(UserSimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'followers_count'
    VALUES = (
        ('lt_1', 'Нет подписчиков'),
        ('gt_1', 'Есть подписчики'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'followers__isnull': True},
        gt_1={'followers__isnull': False}
    )


class AuthorsFilter(UserSimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'authors_count'
    VALUES = (
        ('lt_1', 'Нет подписок'),
        ('gt_1', 'Есть подписки'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'authors__isnull': True},
        gt_1={'authors__isnull': False}
    )


class RecipesFilter(UserSimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'recipe_count'
    VALUES = (
        ('lt_1', 'Нет рецептов'),
        ('gt_1', 'Есть рецепты'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'recipes__isnull': True},
        gt_1={'recipes__isnull': False}
    )


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'full_name',
                    'avatar_override', 'followers_count',
                    'authors_count', 'recipe_count')
    search_fields = ('email', 'username',)
    readonly_fields = ('avatar_override', 'password_change')
    list_filter = (FollowersFilter, AuthorsFilter, RecipesFilter)
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username',)}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'password_change'
        )}),
        (_('Аватар'), {'fields': ('avatar', 'avatar_override')}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    @admin.display(description='Изменение пароля')
    @mark_safe
    def password_change(self, user):
        url = reverse('admin:auth_user_password_change', args=(user.id,))
        return f'<a href="{url}">Изменить пароль</a>'

    @admin.display(description='Полное имя')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписки')
    def authors_count(self, user):
        return user.authors.count()

    @admin.display(description='Рецепты')
    @mark_safe
    def recipe_count(self, user):
        count = user.recipes.count()
        if count > 0:
            url = f'{reverse("api:recipes-list")}?author={user.id}'
            return f'<a href="{url}">{count}</a>'
        return count

    @admin.display(description='Аватар')
    def avatar_override(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" width="100" height="100"/>'
            )
        return 'Нет изображения'
