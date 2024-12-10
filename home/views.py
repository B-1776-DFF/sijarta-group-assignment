from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
import datetime
from django.http import HttpResponse
import uuid

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
            return redirect('homepage')

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
    SELECT serviceTrId, orderDate, TotalPrice, serviceCategoryId, discountCode, paymentMethod
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
        return render(request, 'myorders.html', context)

    except Exception as e:
        print(request, "Unable to fetch orders. Please try again.")
        return redirect('homepage')
    
        
# def book_service(request):
#     user_id = request.session.get('user_id')  # Get user ID from session
#     if not user_id:
#         return redirect('login')  # Redirect to login if user is not authenticated

#     if request.method == 'POST':
#         order_date = datetime.datetime.today()  # Automatically set the current date
#         discount_code = request.POST.get('discount_code', None)
#         payment_method = request.POST.get('payment_method')
#         total_payment = request.POST.get('total_payment')
#         service_category_id = request.POST.get('service_category_id')

#         # Insert the new service order into the database
#         insert_service_order = """
#         INSERT INTO sijartagroupassignment.TR_SERVICE_ORDER (
#             orderDate, serviceDate, serviceTime, TotalPrice, 
#             customerId, serviceCategoryId, discountCode, paymentMethodId
#         ) VALUES (%s, NULL, NULL, %s, %s, %s, %s, %s);
#         """
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute(insert_service_order, [
#                     order_date, total_payment, user_id,
#                     service_category_id, discount_code, payment_method
#                 ])
#                 # Get the last inserted ID (serviceTrId)
#                 service_tr_id = cursor.lastrowid

#                 # Insert the initial status for the service order
#                 insert_order_status = """
#                 INSERT INTO sijartagroupassignment.TR_ORDER_STATUS (
#                     serviceTrId, statusId, date
#                 ) VALUES (%s, %s, %s);
#                 """
#                 # Assume "1" corresponds to the initial status "Waiting for Payment"
#                 cursor.execute(insert_order_status, [service_tr_id, 1, order_date])

#             # Prepare the data to return to the template
#             context = {
#                 'order_id': service_tr_id,  # The ID of the newly created service order
#                 'total_payment': total_payment,
#                 'service_category_id': service_category_id,
#                 'order_date': order_date.strftime('%Y-%m-%d %H:%M:%S'),
#             }

#             messages.success(request, "Service order created successfully!")
#             return render(request, 'myorder.html', context)  # Return data to the template

#         except Exception as e:
#             messages.error(request, "Unable to create service order. Please try again.")
#             return redirect('myorder')

#     # Default template rendering when GET request is made
#     return render(request, 'myorder.html', {'today_date': datetime.datetime.today().strftime('%Y-%m-%d')})


# def my_orders(request):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    # Check if the user is authenticated
    user_id = request.session.get('user_id')
    print(user_id)
    if not user_id:
        return redirect('login')  # Redirect to login if user is not authenticated

    if request.method == "POST":
        # Handle the creation of a new service order
        order_date = datetime.now()  # Automatically set the current date
        discount_code = request.POST.get('discount_code', None)
        payment_method = request.POST.get('payment_method')  # Dropdown value
        service_category_id = request.POST.get('service_category_id')  # Hidden input or passed value
        total_payment = request.POST.get('total_payment')

        # Insert the new service order into the database
        insert_service_order = """
        INSERT INTO sijartagroupassignment.TR_SERVICE_ORDER (
            orderDate, serviceDate, serviceTime, TotalPrice, 
            customerId, serviceCategoryId, discountCode, paymentMethodId
        ) VALUES (%s, NULL, NULL, %s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(insert_service_order, [
                    order_date, total_payment, user_id,
                    service_category_id, discount_code, payment_method
                ])
                # Get the last inserted ID (serviceTrId)
                service_tr_id = cursor.lastrowid

                # Insert the initial status for the service order
                insert_order_status = """
                INSERT INTO sijartagroupassignment.TR_ORDER_STATUS (
                    serviceTrId, statusId, date
                ) VALUES (%s, %s, %s);
                """
                # Assume "1" corresponds to the initial status "Waiting for Payment"
                cursor.execute(insert_order_status, [service_tr_id, 1, order_date])

            messages.success(request, "Service order created successfully!")
            return redirect('my_orders')  # Redirect to the same page to view bookings
        except Exception as e:
            print("Error creating service order:", e)
            messages.error(request, "Unable to create service order. Please try again.")

    # Fetch all service orders for the logged-in user
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
    with connection.cursor() as cursor:
        cursor.execute(select_query, [user_id])
        service_orders = cursor.fetchall()

    # Convert to a list of dictionaries for easier use in templates
    orders = []
    for order in service_orders:
        orders.append({
            'id': order[0],
            'service_name': order[1],
            'order_date': order[2].strftime('%Y-%m-%d') if order[2] else None,
            'total_payment': order[3],
            'discount_code': order[4],
            'payment_method': order[5],  # Map ID to name if needed
            'status': order[6]
        })
    
    print("User ID:", user_id)
    print("Orders:", orders)    
    return render(request, 'myorder.html', {'service_orders': orders})


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