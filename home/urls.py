from django.urls import path
from . import views

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('subcategory/<uuid:subcategory_id>/Customer/', views.subcategory_user, name='subcategory_user'),
    path('subcategory/<uuid:subcategory_id>/Worker/', views.subcategory_worker, name='subcategory_worker'),
    path('myorders/', views.my_orders, name='myorder'),
    path('worker/<uuid:worker_id>/', views.worker_profile_view, name='worker_profile'),
    path('cancel_service_order/', views.cancel_service_order, name='cancel_service_order'),
    path('order/', views.book_service, name='book_service'),
    path('submit_testimonial/', views.submit_testimonial, name='submit_testimonial'),

]
