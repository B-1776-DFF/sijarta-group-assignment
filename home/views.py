from django.shortcuts import render, redirect
from django.db import connection, transaction
from django.contrib import messages
import datetime
from django.http import HttpResponse, JsonResponse
import uuid
from time import timezone

def homepage(request):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
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

    user_role = request.session.get('user_role', 'user')
    
    return render(request, "homepage.html", {"categories": categories, "user_role": user_role})


def subcategory_user(request, subcategory_id):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SET SEARCH_PATH TO sijartagroupassignment;
            WITH WorkerRatings AS (
                SELECT 
                    tso.workerId AS Worker_ID,
                    COALESCE(SUM(t.rating) * 1.0 / COUNT(t.rating), 0) AS Average_Rating
                FROM 
                    tr_service_order tso
                LEFT JOIN 
                    testimoni t
                ON 
                    tso.id = t.serviceTrId
                GROUP BY 
                    tso.workerId
            )
            UPDATE worker w
            SET 
                Rate = wr.Average_Rating
            FROM 
                WorkerRatings wr
            WHERE 
                w.ID = wr.Worker_ID AND w.ID = %s;
            """, [uuid])


        cursor.execute("""            
        SET SEARCH_PATH to sijartagroupassignment;
        SELECT COUNT(*) FROM TR_SERVICE_ORDER WHERE workerid = %s;
        """, [uuid])
        finished_order = cursor.fetchone()[0]

        cursor.execute("""
        SET SEARCH_PATH TO sijartagroupassignment;
        UPDATE WORKER
        SET totalfinishorder = %s
        WHERE id = %s;
        """, [finished_order, uuid])
    
    # Check if the user is authenticated and if they are a customer
    user_role = request.session.get('user_role')
    if user_role != 'Customer':
        return redirect('homepage')  # Redirect to homepage or any other appropriate page
    
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
            w.totalfinishorder AS completed_orders,
            w.id AS worker_id  -- Include worker_id for profile link
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


    print (sessions)
    # Render the user view template with workers and sessions
    return render(request, 'subcategory_user.html', {
        'subcategory_name': subcategory_name,
        'description': description,
        'workers': workers,
        'sessions': sessions,
        'subcategory_id': subcategory_id,
        'today_date': datetime.datetime.today().strftime('%d-%m-%Y')
    })



def subcategory_worker(request, subcategory_id):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    # Check if the user is authenticated and if they are a worker
    user_role = request.session.get('user_role')
    if user_role != 'Worker':
        return redirect('homepage')  # Redirect to homepage or any other appropriate page
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SET SEARCH_PATH TO sijartagroupassignment;
            WITH WorkerRatings AS (
                SELECT 
                    tso.workerId AS Worker_ID,
                    COALESCE(SUM(t.rating) * 1.0 / COUNT(t.rating), 0) AS Average_Rating
                FROM 
                    tr_service_order tso
                LEFT JOIN 
                    testimoni t
                ON 
                    tso.id = t.serviceTrId
                GROUP BY 
                    tso.workerId
            )
            UPDATE worker w
            SET 
                Rate = wr.Average_Rating
            FROM 
                WorkerRatings wr
            WHERE 
                w.ID = wr.Worker_ID AND w.ID = %s;
            """, [uuid])


        cursor.execute("""            
        SET SEARCH_PATH to sijartagroupassignment;
        SELECT COUNT(*) FROM TR_SERVICE_ORDER WHERE workerid = %s;
        """, [uuid])
        finished_order = cursor.fetchone()[0]

        cursor.execute("""
        SET SEARCH_PATH TO sijartagroupassignment;
        UPDATE WORKER
        SET totalfinishorder = %s
        WHERE id = %s;
        """, [finished_order, uuid])
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


def book_service(request):
    user_id = request.session.get('user_id')  # Get user ID from session
    if not user_id:
        return redirect('login')  # Redirect to login if user is not authenticated

    if request.method == 'POST':
        # Fetch form data
        order_date = datetime.datetime.today()
        discount_code = request.POST.get('discount_code', None)
        payment_method_name = request.POST.get('payment_method')  # Name provided from modal
        total_payment = request.POST.get('total_payment')
        
        service_category_id = request.POST.get('service_category_id')

        print("POST data:", request.POST)  # Debugging

        # Validate required fields
        if not total_payment or not service_category_id or not payment_method_name:
            print(request, "All fields are required.")
            return redirect('homepage')

        try:
            # Fetch payment method ID from its name
            query_payment_method_id = """
            SELECT id FROM sijartagroupassignment.PAYMENT_METHOD 
            WHERE name = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query_payment_method_id, [payment_method_name])
                payment_method = cursor.fetchone()
                
                if not payment_method:
                    print(request, "Invalid payment method selected.")
                    return redirect('my_orders')

                payment_method_id = payment_method[0]  # Extract ID

            # Insert new service order
            try:
                with connection.cursor() as cursor:
                    # Step 1: Insert order
                    insert_service_order = """
                    INSERT INTO sijartagroupassignment.TR_SERVICE_ORDER (id,
                        orderDate, serviceDate, serviceTime, TotalPrice, 
                        customerId, serviceCategoryId, discountCode, paymentMethodId
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_service_order, [ uuid.uuid4(),
                        order_date, datetime.datetime.today(), datetime.datetime.now(), total_payment, user_id,
                        service_category_id,  discount_code, payment_method_id
                    ])
                    service_tr_id = cursor.fetchone()[0]

                    # Step 2: Insert initial status
                    insert_order_status = """
                    INSERT INTO sijartagroupassignment.TR_ORDER_STATUS (
                        serviceTrId, statusId, date
                    ) VALUES (%s, %s, %s);
                    """
                    initial_status_id = 1  
                    cursor.execute(insert_order_status, [
                        service_tr_id, initial_status_id, order_date
                    ])

                    # Commit only if both queries succeed
                    connection.commit()

            except Exception as e:
                # Rollback in case of an error
                connection.rollback()
                raise e

            # Success response
            messages.success(request, "Service order created successfully!")
            return render(request, 'myorder.html', {
                'order_id': service_tr_id,
                'total_payment': total_payment,
                'discount_code': discount_code,
                'service_category_id': service_category_id,
                'order_date': order_date.strftime('%Y-%m-%d %H:%M:%S'),
            })

        except Exception as e:
            # Log and display error message
            print("Error creating service order:", e)
            print(request, "An error occurred while creating your order. Please try again.")
            return redirect('myorder')

    # Handle non-POST requests
    return render(request, 'myorder.html', {
        'today_date': datetime.datetime.today().strftime('%Y-%m-%d')
    })

def my_orders(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')  # Redirect to login if user is not authenticated

    # Fetch all orders from the database for the user
    fetch_orders = """
    SELECT Id, orderDate, TotalPrice, serviceCategoryId, discountCode, paymentMethodId
    FROM sijartagroupassignment.TR_SERVICE_ORDER
    WHERE customerId = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(fetch_orders, [user_id])
            orders = cursor.fetchall()

        context = {
            'orders': orders
        }
        print (orders)
        return render(request, 'myorder.html', context)

    except Exception as e:
        print(request, "Unable to fetch orders. Please try again.")
        print("Database Error:", e)
        return redirect('homepage')
    
    

def cancel_service_order(request):
    user_id = request.session.get('user_id')
    
    try:
        select_query = """
            SELECT 
                o.Id AS order_id,
                ss.subcategoryname AS service_name,
                o.orderDate AS order_date,
                o.TotalPrice AS total_payment,
                o.discountCode AS discount_code,
                o.paymentMethodId AS payment_method,
                os.Status AS order_status
            FROM sijartagroupassignment.TR_SERVICE_ORDER o
            JOIN sijartagroupassignment.SERVICE_SUBCATEGORY ss ON o.serviceCategoryId = ss.Id
            JOIN (
                SELECT tos.serviceTrId, MAX(tos.date) AS latest_date
                FROM sijartagroupassignment.TR_ORDER_STATUS tos
                GROUP BY tos.serviceTrId
            ) latest_status ON o.Id = latest_status.serviceTrId
            JOIN sijartagroupassignment.TR_ORDER_STATUS tos ON 
                o.Id = tos.serviceTrId AND tos.date = latest_status.latest_date
            JOIN sijartagroupassignment.ORDER_STATUS os ON tos.statusId = os.Id
            WHERE o.customerId = %s;
            """
        if select_query[6] in ["Waiting for Payment", "Searching for Nearest Workers"]:
            select_query[6] = "Cancelled"
            select_query[6].save()
            return redirect('myorder')  # Redirect to the page that lists orders
        else:
            return HttpResponse("This order cannot be cancelled.", status=400)
    except select_query[6].DoesNotExist:
        return HttpResponse("Order not found or you do not have permission to cancel it.", status=404)
    


    
def worker_profile_view(request, worker_id):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    with connection.cursor() as cursor:

        cursor.execute("""
            SET SEARCH_PATH TO sijartagroupassignment;
            WITH WorkerRatings AS (
                SELECT 
                    tso.workerId AS Worker_ID,
                    COALESCE(SUM(t.rating) * 1.0 / COUNT(t.rating), 0) AS Average_Rating
                FROM 
                    tr_service_order tso
                LEFT JOIN 
                    testimoni t
                ON 
                    tso.id = t.serviceTrId
                GROUP BY 
                    tso.workerId
            )
            UPDATE worker w
            SET 
                Rate = wr.Average_Rating
            FROM 
                WorkerRatings wr
            WHERE 
                w.ID = wr.Worker_ID AND w.ID = %s;
            """, [uuid])
        
        cursor.execute("""            
        SET SEARCH_PATH to sijartagroupassignment;
        SELECT COUNT(*) FROM TR_SERVICE_ORDER WHERE workerid = %s;
        """, [uuid])
        finished_order = cursor.fetchone()[0]

        cursor.execute("""
        SET SEARCH_PATH TO sijartagroupassignment;
        UPDATE WORKER
        SET totalfinishorder = %s
        WHERE id = %s;
        """, [finished_order, uuid])
        
        cursor.execute("""
        SET search_path TO sijartagroupassignment;
        SELECT u.name, u.sex, u.phonenum, u.dob, u.address, w.bankname, w.accnumber, w.npwp, w.picurl, w.rate, w.totalfinishorder
        FROM "USER" u
        JOIN WORKER w ON u.id = w.id
        WHERE u.id = %s;
        """, [worker_id])
        worker = cursor.fetchone()

    if not worker:
        return render(request, '404.html')  # Handle non-existing worker

    context = {
        'worker': {
            'name': worker[0],
            'sex': worker[1],
            'phone_num': worker[2],
            'dob': worker[3],
            'address': worker[4],
            'bank_name': worker[5],
            'acc_number': worker[6],
            'npwp': worker[7],
            'pic_url': worker[8],
            'rate': worker[9],
            'total_finish_order': worker[10]
        }
    }
    return render(request, 'worker_profile.html', context)

def update_rating(worker_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT AVG(t.Rating)
                FROM TESTIMONI t
                JOIN TR_SERVICE_ORDER tso ON t.serviceTrId = tso.id
                WHERE tso.workerId = %s
            """, [worker_id])
            avg_rating = cursor.fetchone()[0]

            if avg_rating is not None:
                cursor.execute("""
                    UPDATE WORKER
                    SET Rate = %s
                    WHERE Id = %s
                """, [avg_rating, worker_id])
                transaction.commit()
    except Exception as e:
        print(f"Error when updating.")

from django.http import JsonResponse

def submit_testimonial(request):
    if request.method == "POST":
        service_tr_id = request.POST.get('serviceTrId')
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        if not service_tr_id or not text or not rating:
            return JsonResponse({'success': False, 'message': 'All fields are required.'})
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT os.Status, tso.workerId
                    FROM TR_ORDER_STATUS tos
                    JOIN ORDER_STATUS os ON tos.statusId = os.Id
                    JOIN TR_SERVICE_ORDER tso ON tos.serviceTrId = tso.Id
                    WHERE tos.serviceTrId = %s
                    ORDER BY tos.date DESC
                    LIMIT 1
                """, [service_tr_id])
                order_status = cursor.fetchone()
                if not order_status or order_status[0] != 'Completed':
                    return JsonResponse({'success': False, 'message': 'Only completed orders can be reviewed.'})
                worker_id = order_status[1]
                cursor.execute("""
                    INSERT INTO TESTIMONI (serviceTrId, date, Text, Rating)
                    VALUES (%s, %s, %s, %s)
                """, [service_tr_id, datetime.datetime.now(), text, rating])
                transaction.commit()
                update_rating(worker_id)
            return JsonResponse({'success': True, 'message': 'Testimonial submitted successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

def delete_testimonial(request):
    if request.method == "POST":
        service_tr_id = request.POST.get('servicetrid')
        print(f"Received servicetrid: {service_tr_id}")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM testimoni 
                    WHERE serviceTrId = %s
                """, [service_tr_id])
                transaction.commit()
            return JsonResponse({'success': True, 'message': 'Testimonial deleted successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})