from django.urls import path
from . import views

urlpatterns = [
    path('', views.discount_view, name='discount'),
]