from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Dummy data for service_jobs
service_orders = [
    {"id": 1, "title": "Home Cleaning", "address": "123 Main St, Anytown", "date": "2023-06-15", "time": "14:00", "status": "Looking for Nearby Worker", "subcategory": "Deep Cleaning", "user_id": 1},
    {"id": 2, "title": "Lawn Mowing", "address": "456 Elm St, Somewhere", "date": "2023-06-16", "time": "10:00", "status": "Assigned", "subcategory": "Grass Cutting", "user_id": 2},
    {"id": 3, "title": "Home Cleaning", "address": "789 Oak St, Nowhere", "date": "2023-06-17", "time": "09:00", "status": "Looking for Nearby Worker", "subcategory": "Regular Cleaning", "user_id": 1},
    {"id": 4, "title": "Window Washing", "address": "321 Pine St, Everywhere", "date": "2023-06-18", "time": "11:00", "status": "Looking for Nearby Worker", "subcategory": "Exterior", "user_id": 3},
    {"id": 5, "title": "Home Cleaning", "address": "654 Birch St, Anywhere", "date": "2023-06-19", "time": "13:00", "status": "Completed", "subcategory": "Deep Cleaning", "user_id": 1},
]

# Dummy data for service_jobs_status
service_jobs_status_orders = [
    {"id": 1, "title": "Home Cleaning", "address": "123 Main St, Anytown", "date": "2023-06-15", "time": "14:00", "status": "Waiting for Worker to Depart", "subcategory": "Deep Cleaning", "user_id": 1},
    {"id": 2, "title": "Lawn Mowing", "address": "456 Elm St, Somewhere", "date": "2023-06-16", "time": "10:00", "status": "Assigned", "subcategory": "Grass Cutting", "user_id": 1},
    {"id": 3, "title": "Window Washing", "address": "321 Pine St, Everywhere", "date": "2023-06-18", "time": "11:00", "status": "Worker Arrived at Location", "subcategory": "Exterior", "user_id": 1},
    {"id": 4, "title": "Home Cleaning", "address": "654 Birch St, Anywhere", "date": "2023-06-19", "time": "13:00", "status": "Service in Progress", "subcategory": "Deep Cleaning", "user_id": 1},
]

categories = {
    "Home Cleaning": ["Deep Cleaning", "Regular Cleaning"],
    "Lawn Mowing": ["Grass Cutting", "Edging"],
    "Window Washing": ["Interior", "Exterior"]
}

def service_jobs(request):
    selected_category = request.GET.get("category", "All")
    selected_subcategory = request.GET.get("subcategory", "All")
    
    filtered_orders = service_orders
    if selected_category != "All":
        filtered_orders = [order for order in filtered_orders if order["title"] == selected_category]
        if selected_subcategory != "All":
            filtered_orders = [order for order in filtered_orders if order["subcategory"] == selected_subcategory]
    
    return render(request, 'service_job.html', {
        'service_orders': filtered_orders,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'categories': categories
    })

def service_jobs_status(request):
    user_id = request.user.id  # Assuming you have user authentication and can get the user ID
    selected_category = request.GET.get("category", "All")
    selected_subcategory = request.GET.get("subcategory", "All")
    
    filtered_orders = [order for order in service_jobs_status_orders if order["user_id"] == user_id]
    if selected_category != "All":
        filtered_orders = [order for order in filtered_orders if order["title"] == selected_category]
        if selected_subcategory != "All":
            filtered_orders = [order for order in filtered_orders if order["subcategory"] == selected_subcategory]
    
    return render(request, 'service_job_status.html', {
        'service_orders': filtered_orders,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'categories': categories
    })