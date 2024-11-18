from django.contrib import admin
from .models import Subcategory, Worker, Testimonial, ServiceSession

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('subcategory', 'user', 'feedback')

@admin.register(ServiceSession)
class ServiceSessionAdmin(admin.ModelAdmin):
    list_display = ('subcategory', 'name', 'price')
