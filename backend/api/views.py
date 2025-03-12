from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilterSet, RecipeFilterSet
from api.paginators import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FoodgramUserSerializer, IngredientSerializer,
    ReadRecipeSerializer, RecipeSerializer, SmallRecipeSerializer,
    UserSubscribingSerializer, TagSerializer
)
from api.shopping_cart import form_shopping_cart
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShopingCart, Subscription, Tag
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = (
        IsAuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def favorite_and_shopping_add(pk, model, request, message):
        item, created = model.objects.get_or_create(
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        )
        if not created:
            raise ValidationError(f'Данный рецепт уже в {message}!')
        return Response(
            SmallRecipeSerializer(item.recipe).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def favorite_and_shopping_delete(pk, model, request, message):
        get_object_or_404(model, user=request.user, recipe_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.favorite_and_shopping_add(
            pk, Favorite, request, 'избранном'
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self.favorite_and_shopping_delete(
            pk, Favorite, request, 'избранном'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self.favorite_and_shopping_add(
            pk, ShopingCart, request, 'корзине'
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.favorite_and_shopping_delete(
            pk, ShopingCart, request, 'корзине'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        shoping_cart = ShopingCart.objects.filter(
            user=request.user
        ).values('recipe', 'recipe__name')
        recipes = [item['recipe'] for item in shoping_cart]
        recipes_names = [item['recipe__name'] for item in shoping_cart]
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        return FileResponse(
            form_shopping_cart(recipes_names, ingredients),
            as_attachment=True,
            filename='cart.txt'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_link(self, request, pk):
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(
                f'Рецепта с id {pk} не существует!'
            )
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse("recipes:short_link", args=[pk])
            )},
            status=status.HTTP_200_OK
        )


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = FoodgramPagination
    permission_classes = []

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated(), ]
        return super().get_permissions()

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        if not request.data.get('avatar'):
            raise ValidationError('Отсутсвует файл!')
        serializer = FoodgramUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid()
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def avatar_delete(self, request):
        if request.user.avatar is None:
            raise ValidationError('Аватар не установлен!')
        request.user.avatar.delete()
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions_items = request.user.followers.all()
        subscriptions = [
            subscription.author for subscription in subscriptions_items
        ]
        paginator = self.paginate_queryset(subscriptions)
        return self.get_paginated_response(
            UserSubscribingSerializer(
                paginator,
                context={'request': request},
                many=True
            ).data
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if author == request.user:
            raise ValidationError('Нельзя подписаться на самого себя!')
        subscription, created = Subscription.objects.get_or_create(
            follower=request.user,
            author=author
        )
        if not created:
            raise ValidationError(
                f'Вы уже подписаны на пользователя {author.username}!'
            )
        return Response(
            UserSubscribingSerializer(
                subscription.author,
                context={
                    'request': request,
                }
            ).data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        get_object_or_404(Subscription, follower=request.user, author_id=id)
        return Response(status=status.HTTP_204_NO_CONTENT)
