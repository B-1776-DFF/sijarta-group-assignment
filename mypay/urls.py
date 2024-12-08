from django.urls import path
from mypay.views import *

app_name = 'mypay'

urlpatterns = [
    path('', mypay_view, name='mypay'),
    path('transaction', mypay_transactions, name='transaction'),
]
