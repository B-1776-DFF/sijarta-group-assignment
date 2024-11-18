from django.urls import path
from service_jobs.views import service_jobs, service_jobs_status
urlpatterns = [
    path('', service_jobs, name='service_jobs'),
    path('status/', service_jobs_status, name='service_jobs_status'),
]