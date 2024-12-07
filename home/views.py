from django.shortcuts import render, redirect
from django.db import connection



# Homepage
from django.db import connection

def homepage(request):
    query = """
    SELECT 
        sc.id AS category_id,
        sc.categoryname AS category_name,
        ssc.id AS subcategory_id,
        ssc.subcategoryname AS subcategory_name
    FROM 
        sijartagroupassignment.service_category sc
    LEFT JOIN 
        sijartagroupassignment.service_subcategory ssc
    ON 
        sc.id = ssc.servicecategoryid;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    categories = {}
    for row in rows:
        category_id, category_name, subcategory_id, subcategory_name = row
        if category_name not in categories:
            categories[category_name] = []
        if subcategory_id:
            categories[category_name].append({"id": subcategory_id, "name": subcategory_name})

    return render(request, "homepage.html", {"categories": categories})


def subcategory_user(request, subcategory_id):
    # Fetch subcategory details
    query_subcategory = """
    SELECT id, subcategoryname, description 
    FROM sijartagroupassignment.service_subcategory 
    WHERE id = %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query_subcategory, [str(subcategory_id)])
        subcategory = cursor.fetchone()

    if not subcategory:
        # Handle non-existing subcategory
        return render(request, '404.html')

    subcategory_name, description = subcategory[1], subcategory[2]

    # Fetch workers in this subcategory
    query_workers = """
    SELECT w.id AS worker_id, 
           w.picurl AS profile_picture, 
           w.rate AS worker_rate, 
           w.totalfinishorder
    FROM sijartagroupassignment.worker w
    JOIN sijartagroupassignment.worker_service_category wsc
        ON w.id = wsc.workerid
    WHERE wsc.servicecategoryid = %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query_workers, [str(subcategory_id)])
        workers = cursor.fetchall()

    # Fetch available service sessions for this subcategory
    query_sessions = """
    SELECT ss.subcategoryid AS subcategory_id, 
           ss.session AS session_number, 
           ss.price
    FROM sijartagroupassignment.service_session ss
    WHERE ss.subcategoryid = %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query_sessions, [str(subcategory_id)])
        sessions = cursor.fetchall()

    # Render the user view template
    return render(request, 'subcategory_user.html', {
        'subcategory_name': subcategory_name,
        'description': description,
        'workers': workers,
        'sessions': sessions,
        'subcategory_id': subcategory_id
    })


def subcategory_worker(request, subcategory_id):
    # Check if the user is associated with the worker table
    user_is_worker = False
    if request.user.is_authenticated:
        query_worker = """
        SELECT id 
        FROM sijartagroupassignment.worker 
        WHERE user_id = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query_worker, [request.user.id])
            worker = cursor.fetchone()
            user_is_worker = worker is not None

    if user_is_worker:
        # Worker-specific logic
        query_subcategory = """
        SELECT id, subcategoryname, description 
        FROM sijartagroupassignment.service_subcategory 
        WHERE id = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query_subcategory, [str(subcategory_id)])
            subcategory = cursor.fetchone()

        if not subcategory:
            return render(request, '404.html')  # Handle non-existing subcategory

        subcategory_name, description = subcategory[1], subcategory[2]

        # Fetch sessions for the worker
        query_sessions = """
        SELECT ss.id AS session_id, ss.session_name, ss.price 
        FROM sijartagroupassignment.service_session ss
        JOIN sijartagroupassignment.worker_service_category wsc
            ON ss.subcategory_id = wsc.subcategory_id
        WHERE wsc.worker_id = %s AND ss.subcategory_id = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query_sessions, [worker[0], str(subcategory_id)])
            sessions = cursor.fetchall()

        # Render the worker-specific page
        return render(request, 'subcategory_worker.html', {
            'subcategory_name': subcategory_name,
            'description': description,
            'sessions': sessions,
            'subcategory_id': subcategory_id,
        })

    # If not a worker, redirect to the customer page
    return redirect('/subcategory/{}/user/'.format(subcategory_id))
