from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_item', views.get_item, name='get_item'),
]