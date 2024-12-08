from django.shortcuts import render, redirect
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
    # Fetch subcategory details (name and description)
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

    # Step 1: Get servicecategoryid for the given subcategory_id
    query_servicecategoryid = """
    SELECT servicecategoryid 
    FROM sijartagroupassignment.service_subcategory
    WHERE id = %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query_servicecategoryid, [str(subcategory_id)])
        servicecategoryid = cursor.fetchone()

    if not servicecategoryid:
        return render(request, '404.html')  # Handle error if servicecategoryid not found

    servicecategoryid = servicecategoryid[0]

    # Step 2: Fetch workers associated with the service category
    query_workers = """
        SELECT 
            u.name AS worker_name,  -- Fetch worker's name from the USER table
            w.picurl AS profile_picture, 
            w.rate AS worker_rate, 
            w.totalfinishorder AS completed_orders
        FROM sijartagroupassignment.worker w
        JOIN sijartagroupassignment."USER" u
            ON w.id = u.id  -- Join on the worker ID to get the worker's name
        WHERE w.id IN (
            SELECT workerid
            FROM sijartagroupassignment.worker_service_category
            WHERE servicecategoryid = %s
        );
        """

    with connection.cursor() as cursor:
        cursor.execute(query_workers, [str(servicecategoryid)])
        workers = cursor.fetchall()

    # Fetch available service sessions for this subcategory (Optional: If you still need session data)
    query_sessions = """
    SELECT ss.session AS session_number, 
           ss.price AS session_price
    FROM sijartagroupassignment.service_session ss
    WHERE ss.subcategoryid = %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query_sessions, [str(subcategory_id)])
        sessions = cursor.fetchall()

    # Render the user view template with workers and sessions
    return render(request, 'subcategory_user.html', {
        'subcategory_name': subcategory_name,
        'description': description,
        'workers': workers,
        'sessions': sessions,
        'subcategory_id': subcategory_id
    })


def subcategory_worker(request, subcategory_id):
    # Initialize the user_is_worker flag and worker variable
    user_is_worker = False
    worker = None

    # Check if the user is authenticated and if they are a worker
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

    # Fetch subcategory info
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
    
    # Fetch sessions for the subcategory
    query_sessions = """
        SELECT ss.session AS session_number, 
            ss.price AS session_price
        FROM sijartagroupassignment.service_session ss
        WHERE ss.subcategoryid = %s;
        """
    with connection.cursor() as cursor:
        cursor.execute(query_sessions, [str(subcategory_id)])
        sessions = cursor.fetchall()

    # Fetch available workers for this subcategory along with the worker's name from the user table
    query_workers = """
    SELECT w.id, u.name AS worker_name, w.picurl, w.rate AS worker_rate
    FROM sijartagroupassignment.worker w
    JOIN sijartagroupassignment.worker_service_category wsc
        ON w.id = wsc.workerid
    JOIN sijartagroupassignment."USER" u ON w.id = u.id  -- Join USER table to get the worker's name
    JOIN sijartagroupassignment.service_category sc 
        ON wsc.servicecategoryid = sc.id
    JOIN sijartagroupassignment.service_subcategory ss 
        ON sc.id = ss.servicecategoryid  
    WHERE ss.id = %s;  -- Filter by subcategory ID
    """

    with connection.cursor() as cursor:
        cursor.execute(query_workers, [str(subcategory_id)])
        workers = cursor.fetchall()

    # Check if the current worker is already joined to this subcategory
    user_is_joined = False
    if user_is_worker and worker:
        query_check_join = """
        SELECT 1 
        FROM sijartagroupassignment.worker_service_category 
        WHERE workerid = %s AND subcategory_id = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query_check_join, [worker[0], str(subcategory_id)])
            user_is_joined = cursor.fetchone() is not None

    # Render the page with all the necessary data
    return render(request, 'subcategory_worker.html', {
        'subcategory_name': subcategory_name,
        'description': description,
        'sessions': sessions,
        'workers': workers,
        'subcategory_id': subcategory_id,
        'user_is_worker': user_is_worker,
        'user_is_joined': user_is_joined,
    })

def book_service (request, session_id):
    pass