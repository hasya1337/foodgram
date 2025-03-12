from django.urls import path

from recipes.views import decode_link

app_name = 'recipes'

urlpatterns = [
    path('s/<int:id>', decode_link, name='short_link')
]
