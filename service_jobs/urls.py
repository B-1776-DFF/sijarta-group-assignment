from django.urls import path
from service_jobs.views import *
urlpatterns = [
    path('', service_jobs, name='service_jobs'),
    path('accept_job', accept_job, name='accept_job'),
]