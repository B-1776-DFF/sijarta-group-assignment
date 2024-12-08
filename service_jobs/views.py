from django.shortcuts import render
from django.db import connection, transaction
from django.http import JsonResponse
from datetime import datetime
import json

def service_jobs(request):
    worker_id = '38297fec-b4c2-4991-8dde-e97df30ef1e8'
    
    # Fetch service categories for the worker
    category_query = """
    SET search_path TO sijartagroupassignment;
    SELECT wsc.serviceCategoryId, sc.CategoryName
    FROM worker_service_category AS wsc
    LEFT JOIN service_category AS sc ON wsc.serviceCategoryId = sc.Id
    WHERE wsc.workerId = %s
    """
    
    selected_category = request.GET.get('category', 'All')
    selected_subcategory = request.GET.get('subcategory', 'All')
    query_params = [worker_id]

    # Modified order query to only show Processing orders
    order_query = """
    SET search_path TO sijartagroupassignment;
    SELECT DISTINCT tso.Id, 
        sub.SubcategoryName,
        u.name AS customer_name,
        tso.orderDate,
        tso.serviceDate,
        tso.Session,
        tso.TotalPrice,
        os.Status
    FROM tr_service_order tso
    JOIN tr_order_status tos ON tso.Id = tos.serviceTrId
    JOIN order_status os ON tos.statusId = os.Id
    JOIN service_subcategory sub ON tso.serviceCategoryId = sub.Id
    JOIN service_category sc ON sub.ServiceCategoryId = sc.Id
    JOIN customer c ON tso.customerId = c.Id
    JOIN "USER" u ON c.Id = u.Id
    JOIN worker_service_category wsc ON sc.Id = wsc.serviceCategoryId
    WHERE wsc.workerId = %s
    AND os.Status = 'Processing'
    AND tos.date = (
        SELECT MAX(date)
        FROM tr_order_status
        WHERE serviceTrId = tso.Id
    )
    """

    if selected_category != "All":
        order_query += " AND sc.Id = %s"
        query_params.append(selected_category)
    if selected_subcategory != "All":
        order_query += " AND sub.Id = %s"
        query_params.append(selected_subcategory)

    with connection.cursor() as cursor:
        cursor.execute(category_query, [worker_id])
        worker_service_categories = cursor.fetchall()
        
        cursor.execute(order_query, query_params)
        orders = cursor.fetchall()

    return render(request, 'service_job.html', {
        'orders': orders,
        'worker_service_categories': worker_service_categories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
    })

@transaction.atomic
def accept_job(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            worker_id = '38297fec-b4c2-4991-8dde-e97df30ef1e8'

            with connection.cursor() as cursor:
                # First check if order is still available
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    SELECT COUNT(*) 
                    FROM tr_service_order tso
                    JOIN tr_order_status tos ON tso.Id = tos.serviceTrId
                    JOIN order_status os ON tos.statusId = os.Id
                    WHERE tso.Id = %s
                    AND os.Status = 'Processing'
                    AND tos.date = (
                        SELECT MAX(date)
                        FROM tr_order_status
                        WHERE serviceTrId = %s
                    )
                """, [order_id, order_id])
                
                if cursor.fetchone()[0] == 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'This order is no longer available.'
                    })

                # Get Waiting status ID
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    SELECT Id FROM order_status WHERE Status = 'Waiting'
                """)
                waiting_status_id = cursor.fetchone()[0]

                # Insert new status record
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    INSERT INTO tr_order_status (serviceTrId, statusId, date)
                    VALUES (%s, %s, %s)
                """, [order_id, waiting_status_id, datetime.now()])

                # Update worker assignment
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    UPDATE tr_service_order
                    SET workerId = %s
                    WHERE Id = %s
                """, [worker_id, order_id])

            return JsonResponse({
                'success': True,
                'message': 'Job accepted successfully. You can view it in your job status page.'
            })

        except Exception as e:
            print(f"Error in accept_job: {str(e)}")  # Debug log
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def service_job_status(request):
    worker_id = '38297fec-b4c2-4991-8dde-e97df30ef1e8'
    selected_category = request.GET.get('category', 'All')
    selected_status = request.GET.get('status', 'All')
    
    query = """
    SET search_path TO sijartagroupassignment;
    SELECT DISTINCT
        tso.Id,
        sub.SubcategoryName,
        u.name AS customer_name,
        tso.orderDate,
        tso.serviceDate,
        tso.serviceTime,
        tso.TotalPrice,
        os.Status AS current_status,
        os.Id AS status_id,
        sub.Id AS subcategory_id,
        sc.CategoryName,
        sc.Id as category_id,
        CASE os.Status 
            WHEN 'Waiting' THEN 1
            WHEN 'Arrived' THEN 2
            WHEN 'Ongoing' THEN 3
            WHEN 'Completed' THEN 4
            ELSE 5
        END as status_order
    FROM tr_service_order tso
    JOIN tr_order_status tos ON tso.Id = tos.serviceTrId
    JOIN order_status os ON tos.statusId = os.Id
    JOIN service_subcategory sub ON tso.serviceCategoryId = sub.Id
    JOIN service_category sc ON sub.ServiceCategoryId = sc.Id
    JOIN customer c ON tso.customerId = c.Id
    JOIN "USER" u ON c.Id = u.Id
    WHERE tso.workerId = %s
    AND tos.date = (
        SELECT MAX(date)
        FROM tr_order_status
        WHERE serviceTrId = tso.Id
    )
    """
    
    query_params = [worker_id]
    
    # Fix category filter by using ServiceCategoryId from subcategory table
    if selected_category != 'All':
        query += " AND sub.ServiceCategoryId::text = %s"
        query_params.append(selected_category)
    
    status_map = {
        'Waiting': ['Waiting'],
        'Arrived': ['Arrived'],
        'InProgress': ['Ongoing'],
        'Completed': ['Completed']
    }
    
    if selected_status != 'All' and selected_status in status_map:
        query += " AND os.Status = %s"
        query_params.append(status_map[selected_status][0])
    
    query += """
    ORDER BY 
        status_order,
        tso.serviceDate ASC,
        tso.serviceTime ASC
    """
    
    # Get categories for filter dropdown
    category_query = """
    SET search_path TO sijartagroupassignment;
    SELECT sc.Id, sc.CategoryName 
    FROM worker_service_category wsc
    JOIN service_category sc ON wsc.serviceCategoryId = sc.Id
    WHERE wsc.workerId = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, query_params)
        orders = cursor.fetchall()
        
        cursor.execute(category_query, [worker_id])
        categories = cursor.fetchall()

    return render(request, 'service_job_status.html', {
        'orders': orders,
        'categories': categories,
        'selected_category': selected_category,
        'selected_status': selected_status
    })

@transaction.atomic
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('new_status')

            # Define valid status transitions
            valid_transitions = {
                'Waiting': ['Arrived'],
                'Arrived': ['Ongoing'],
                'Ongoing': ['Completed']
            }

            with connection.cursor() as cursor:
                # Get current status
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    SELECT os.Status
                    FROM tr_order_status tos
                    JOIN order_status os ON tos.statusId = os.Id
                    WHERE tos.serviceTrId = %s
                    AND tos.date = (
                        SELECT MAX(date)
                        FROM tr_order_status
                        WHERE serviceTrId = %s
                    )
                """, [order_id, order_id])
                
                current_status = cursor.fetchone()[0]

                # Validate status transition
                if current_status not in valid_transitions or new_status not in valid_transitions[current_status]:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Invalid status transition from {current_status} to {new_status}'
                    })

                # Insert new status
                cursor.execute("""
                    SET search_path TO sijartagroupassignment;
                    INSERT INTO tr_order_status (serviceTrId, statusId, date)
                    VALUES (%s, (SELECT Id FROM order_status WHERE Status = %s), %s)
                """, [order_id, new_status, datetime.now()])

                return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})