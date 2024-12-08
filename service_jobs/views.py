from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from datetime import datetime
import json

def service_jobs(request):
    worker_id = '26b7d02c-6d45-4630-a848-e8a84494eeeb'

    # Fetch service categories for the worker
    category_query = """
    SET search_path TO sijartagroupassignment;
    SELECT wsc.serviceCategoryId, sc.CategoryName
    FROM worker_service_category AS wsc
    LEFT JOIN service_category AS sc ON wsc.serviceCategoryId = sc.Id
    WHERE wsc.workerId = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(category_query, [worker_id])
        worker_service_categories = cursor.fetchall()

    selected_category = request.GET.get('category', 'All')
    selected_subcategory = request.GET.get('subcategory', 'All')

    # Fetch subcategories based on the selected category
    subcategory_query = """
    SET search_path TO sijartagroupassignment;
    SELECT subcategory.id::text, subcategory.SubcategoryName, subcategory.ServiceCategoryId::text
    FROM service_subcategory AS subcategory
    WHERE (%s = 'All' OR subcategory.ServiceCategoryId::text = %s)
    """
    with connection.cursor() as cursor:
        cursor.execute(subcategory_query, [selected_category, selected_category])
        subcategories = cursor.fetchall()

    # Fetch service orders
    order_query = """
    SET search_path TO sijartagroupassignment;
    SELECT tso.Id, tso.serviceCategoryId::text, sc.CategoryName, tso.orderDate, tso.TotalPrice, tso.serviceTime,
        os.Status AS order_status, ss.Session, ss.Price
    FROM tr_service_order AS tso
    LEFT JOIN tr_order_status AS tos ON tso.Id = tos.serviceTrId
    LEFT JOIN order_status AS os ON tos.statusId = os.Id
    LEFT JOIN service_session ss ON tso.serviceCategoryId = ss.SubcategoryId AND tso.Session = ss.Session
    LEFT JOIN service_subcategory sub ON ss.SubcategoryId = sub.Id
    LEFT JOIN service_category sc ON sub.ServiceCategoryId = sc.Id
    WHERE tso.workerId = %s
    AND os.Status = 'Looking for Nearby Worker'
    AND tos.date = (
        SELECT MAX(date)
        FROM tr_order_status
        WHERE serviceTrId = tso.Id
    )
    """
    query_params = [worker_id]
    if selected_category != "All":
        order_query += " AND sub.ServiceCategoryId = %s"
        query_params.append(selected_category)
    if selected_subcategory != "All":
        order_query += " AND ss.SubcategoryId = %s"
        query_params.append(selected_subcategory)

    with connection.cursor() as cursor:
        cursor.execute(order_query, query_params)
        orders = cursor.fetchall()

    return render(request, 'service_job.html', {
        'orders': orders,
        'subcategories': subcategories,
        'worker_service_categories': worker_service_categories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
    })

def accept_job(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            worker_id = '26b7d02c-6d45-4630-a848-e8a84494eeeb'
            update_status_query = """
            SET search_path TO sijartagroupassignment;
            INSERT INTO tr_order_status (serviceTrId, statusId, date)
            VALUES (%s, (
                SELECT Id FROM order_status WHERE Status = 'Accepted'
            ), %s)
            """
            with connection.cursor() as cursor:
                cursor.execute(update_status_query, [order_id, datetime.now()])
            return JsonResponse({"success": True, "message": "Job accepted successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid request method."})
