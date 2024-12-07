from django.urls import path
from . import views

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('subcategory/<int:subcategory_id>/user/', views.subcategory_user_view, name='subcategory_user'),
    path('subcategory/<int:subcategory_id>/worker/', views.subcategory_worker_view, name='subcategory_worker'),
    path('subcategory/<int:subcategory_id>/join/', views.join_subcategory, name='join_subcategory'),
    path('book-session/<int:session_id>/', views.book_session, name='book_session'),
    path('subcategory/<int:subcategory_id>/workers/json', views.subcategory_worker_view_json, name='subcategory_worker_view_json'),

]
