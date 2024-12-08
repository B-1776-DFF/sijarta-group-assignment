from django.urls import path
from . import views

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('subcategory/<uuid:subcategory_id>/user/', views.subcategory_user, name='subcategory_user'),
    path('subcategory/<uuid:subcategory_id>/worker/', views.subcategory_worker, name='subcategory_worker'),
    path('myorders/', views.my_orders, name='myorder'),
    path('worker/<uuid:worker_id>/', views.worker_profile_view, name='worker_profile'),
    # path('subcategory/<int:subcategory_id>/join/', views.join_subcategory, name='join_subcategory'),
    # path('book-session/<int:session_id>/', views.book_session, name='book_session'),

]
