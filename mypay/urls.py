from django.urls import path
from mypay.views import mypay_view

app_name = 'mypay'

urlpatterns = [
    path('', mypay_view, name='mypay'),
]
