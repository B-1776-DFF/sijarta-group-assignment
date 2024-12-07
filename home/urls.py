from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('subcategory/<uuid:subcategory_id>/user/', views.subcategory_user, name='subcategory_user'),
    path('subcategory/<uuid:subcategory_id>/worker/', views.subcategory_worker, name='subcategory_worker'),
    # path('subcategory/<int:subcategory_id>/join/', views.join_subcategory, name='join_subcategory'),
    # path('book-session/<int:session_id>/', views.book_session, name='book_session'),

]
