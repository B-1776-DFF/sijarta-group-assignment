from django.urls import path
from . import views

urlpatterns = [
    path('', views.discount_view, name='discount'),
    path('get_user_balance/', views.get_user_balance, name='get_user_balance')
]