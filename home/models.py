from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from datetime import datetime
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subcategories = models.ManyToManyField(Subcategory, related_name='workers')

    def __str__(self):
        return self.user.username


class Testimonial(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='testimonials')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    worker_name = models.CharField(max_length=255, null=True, blank=True)  # Add this if needed
    rating = models.FloatField(null=True, blank=True)  # Add this if needed
    created_at = models.DateTimeField(auto_now_add=True)



class ServiceSession(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='service_sessions')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(ServiceSession, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
        default='pending'
    )

    def __str__(self):
        return f"Booking by {self.user.username} for {self.session.name}"

