from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/user/', views.register_user_view, name='register_user'),
    path('register/worker/', views.register_worker_view, name='register_worker'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('', views.homepage, name='landingpage')
]
