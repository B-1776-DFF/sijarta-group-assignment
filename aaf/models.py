import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    phone_num = models.CharField(max_length=15, unique=True)
    pwd = models.CharField(max_length=255)  # Store hashed passwords
    dob = models.DateField()
    address = models.TextField()
    mypay_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Customer(models.Model):
    id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    level = models.CharField(max_length=50, default="Standard")

    def __str__(self):
        return f"Customer: {self.id.name}"

class Worker(models.Model):
    id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    bank_name = models.CharField(max_length=100)
    acc_number = models.CharField(max_length=50, unique=True)
    npwp = models.CharField(max_length=20, unique=True)
    pic_url = models.URLField()
    rate = models.FloatField(default=0.0)
    total_finish_order = models.IntegerField(default=0)

    def __str__(self):
        return f"Worker: {self.id.name}"
