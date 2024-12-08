from django.urls import path
from service_jobs.views import *

app_name = 'service_jobs'

urlpatterns = [
    path('', service_jobs, name='service_jobs'),
    path('accept_job/', accept_job, name='accept_job'),
    path('status/', service_job_status, name='service_job_status'),
    path('update_status/', update_order_status, name='update_order_status'),  
]