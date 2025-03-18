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
    def manage_favorite_or_cart(pk, model, request, action):
        recipe = get_object_or_404(Recipe, id=pk)
        if action == 'add':
            item, created = model.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                raise ValidationError(
                    f'Данный рецепт уже в {model._meta.verbose_name}!'
                )
            return Response(
                SmallRecipeSerializer(item.recipe).data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(model, user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.manage_favorite_or_cart(pk, Favorite, request, 'add')

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self.manage_favorite_or_cart(pk, Favorite, request, 'delete')

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self.manage_favorite_or_cart(pk, ShopingCart, request, 'add')

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.manage_favorite_or_cart(pk, ShopingCart, request, 'delete')

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        recipes = request.user.shopping_cart.values_list('recipe', flat=True)
        recipes_names = request.user.shopping_cart.values_list(
            'recipe__name',
            flat=True
        )
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
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
        return Response(
            {
                'short-link': request.build_absolute_uri(reverse(
                    "recipes:short_link",
                    args=[pk])
                )
            },
            status=status.HTTP_200_OK)


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = FoodgramPagination
    permission_classes = []

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        if 'avatar' not in request.data:
            raise ValidationError('Отсутствует файл!')
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def avatar_delete(self, request):
        if not request.user.avatar:
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
        subscriptions = request.user.followers.values_list('author', flat=True)
        paginated_subs = self.paginate_queryset(
            User.objects.filter(
                id__in=subscriptions
            )
        )
        return self.get_paginated_response(UserSubscribingSerializer(
            paginated_subs,
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
        serializer = UserSubscribingSerializer(
            data={'author': author},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(follower=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        get_object_or_404(
            Subscription,
            follower=request.user,
            author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
