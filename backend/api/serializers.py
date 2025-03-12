from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MINIMAL_AMOUNT, MINIMAL_TIME
from recipes.models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, ShopingCart, Subscription, Tag
)


User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def validate_username(username):
        RegexValidator(
            regex=r'^[\w.@+-]+\z',
            message='Логин должен состоять из букв, цифр, знаков .@+-'
        )(username)
        return username

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Subscription.objects.filter(
                follower=request.user, author=author
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=MINIMAL_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MINIMAL_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
        )

    @staticmethod
    def handling_tags_ingredient(recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['ingredient'],
            amount=ingredient['amount']
        ) for ingredient in ingredients)

    @staticmethod
    def fields_validation(data, message):
        if not data:
            raise serializers.ValidationError(f'Отсутствуют {message}ы!')
        items = set()
        for item in data:
            if isinstance(item, dict):
                item = item['ingredient']
            if item in items:
                raise serializers.ValidationError(
                    f'Дублируется {message} {item.name}!')
            items.add(item)
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = super().create(validated_data)
        self.handling_tags_ingredient(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('recipe_ingredients', None)
        tags = validated_data.pop('tags', None)
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
        self.handling_tags_ingredient(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def validate_ingredients(self, ingredients_data):
        return self.fields_validation(ingredients_data, 'продукт')

    def validate_tags(self, tags_data):
        return self.fields_validation(tags_data, 'тег')

    def validate_image(self, image_data):
        if not image_data:
            raise serializers.ValidationError(
                'Нет изображения!')
        return image_data

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    author = FoodgramUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(default=False)
    is_in_shopping_cart = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def fields_acquiring(self, recipe, model):
        user = self.context.get('request').user
        return (
            user is not None
            and not user.is_anonymous
            and model.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_favorited(self, recipe):
        return self.fields_acquiring(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self.fields_acquiring(recipe, ShopingCart)


class SmallRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribingSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = FoodgramUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, author):
        return SmallRecipeSerializer(
            author.recipes.all()[:int(self.context.get(
                'request'
            ).query_params.get('recipes_limit', 100000))],
            many=True,
            context=self.context
        ).data
