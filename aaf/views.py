from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, IntegrityError, DatabaseError, InternalError
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
import uuid

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        print("Phone:", phone, "Password:", password)  # Debug log

        if not phone or not password:
            messages.error(request, "Phone number and password are required.")
            return render(request, 'login.html')

        with connection.cursor() as cursor:
            cursor.execute(rf"""
            SET search_path TO sijartagroupassignment;
            SELECT id, name, pwd FROM "USER" WHERE phonenum = '{phone}'""")
            user = cursor.fetchone()
            print("User fetched:", user)  # Debug log

        if user:
            # Verify the password
            if (password != user[2]) != check_password(password, user[2]):
                messages.error(request, "Incorrect Password!")
                return render(request, 'login.html')
            
            user_id = user[0]  # Assuming this is the UUID
            request.session['user_id'] = str(user_id)
            request.session['user_role'] = None
            request.session['user_phone_num'] = phone
            print("User ID set:", request.session['user_id'])  # Debug log

            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT COUNT(*) FROM WORKER WHERE id = %s;
                """, [user[0]])
                if cursor.fetchone()[0] > 0:
                    request.session['user_role'] = 'Worker'

                cursor.execute("""
                SELECT COUNT(*) FROM CUSTOMER WHERE id = %s;
                """, [user[0]])
                if cursor.fetchone()[0] > 0:
                    request.session['user_role'] = 'Customer'

            print("User role set:", request.session['user_role'])  # Debug log
            return redirect('homepage')

        messages.error(request, "Invalid phone number or password.")
    return render(request, 'login.html')



def logout_view(request):
    request.session.flush()
    return redirect('landingpage')


@csrf_exempt
def register_user_view(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        password = make_password(request.POST.get('password'))
        sex = request.POST.get('sex')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        address = request.POST.get('address')

        # Generate a unique ID for the user
        user_id = str(uuid.uuid4())

        try:
            with connection.cursor() as cursor:
                # Insert the user into the database
                cursor.execute("""
                SET search_path TO sijartagroupassignment;
                INSERT INTO "USER" (id, name, pwd, sex, phonenum, dob, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """, [user_id, name, password, sex, phone, dob, address])
                user_id = cursor.fetchone()[0]

                # Insert into the CUSTOMER table
                cursor.execute("""
                INSERT INTO CUSTOMER (id) VALUES (%s);
                """, [user_id])

            # Success message
            messages.success(request, "User registration successful!")
            return redirect('login')

        except InternalError as e:
            if 'Phone number already registered' in str(e):
                messages.error(request, "The phone number is already registered. Please use a different one.")
            else:
                messages.error(request, "An error occurred during registration. Please try again.")

    return render(request, 'register_user.html')

def register_view(request):
    return render(request, 'register.html')


@csrf_exempt
def register_worker_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = make_password(request.POST.get('password'))
        sex = request.POST.get('sex')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        bank_name = request.POST.get('bank_name')
        acc_number = request.POST.get('acc_number')
        npwp = request.POST.get('npwp')
        pic_url = request.POST.get('pic_url')

        # Generate a unique ID for the user
        user_id = str(uuid.uuid4())

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                SET search_path TO sijartagroupassignment;
                INSERT INTO "USER" (id, name, pwd, sex, phonenum, dob, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """, [user_id, name, password, sex, phone, dob, address])
                user_id = cursor.fetchone()[0]

                cursor.execute("""
                INSERT INTO WORKER (id, bankname, accnumber, npwp, picurl) 
                VALUES (%s, %s, %s, %s, %s);
                """, [user_id, bank_name, acc_number, npwp, pic_url])

            messages.success(request, "Worker registration successful!")
            return redirect('login')

        except InternalError as e:
            if 'Phone number already registered' in str(e):
                messages.error(request, "The phone number is already registered. Please use a different one.")
            else:
                messages.error(request, "An error occurred during registration. Please try again.")

    return render(request, 'register_worker.html')


def profile_view(request):
    uuid = request.session.get('user_id')
    print("Phone number:", uuid)  # Debug log
    if not uuid:
        return redirect('login')

    role = request.session.get('user_role')

    with connection.cursor() as cursor:
        # Fetch user data using phone_num instead of user_id
        cursor.execute("""
        SET search_path TO sijartagroupassignment;
        SELECT * FROM "USER" WHERE id = %s;
        """, [uuid])
        user = cursor.fetchone()

        profile = None
        if role == 'Customer':
            cursor.execute("""
            SELECT * FROM CUSTOMER WHERE id = %s;
            """, [uuid])  # Query profile using phone_num
            profile = cursor.fetchone()
            profile_data = {
                'level': profile[1]
            }
        elif role == 'Worker':
            cursor.execute("""
            SELECT * FROM WORKER WHERE id = %s;
            """, [uuid])  # Query profile using phone_num
            profile = cursor.fetchone()
            profile_data = {
                'bank_name': profile[1],
                'acc_number': profile[2],
                'npwp': profile[3],
                'pic_url': profile[4],
                'rate': profile[5],
                'total_finish_order': profile[6]
            }
        print("Profile fetched:", profile)  # Debug log
        print("Role:", role)  # Debug log
        print("User:", user)  # Debug log

    context = {
        'user': {
            'id': user[0],
            'name': user[1],
            'sex': user[2],
            'phone_num': user[3],
            'pwd': user[4],
            'dob': user[5],
            'address': user[6],
            'mypay_balance': user[7]
        },
        'profile': profile_data,
        'role': role
    }
    return render(request, 'profile.html', context)




@csrf_exempt
def profile_update_view(request):
    user_id = request.session.get('user_id')
    role = request.session.get('user_role')

    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        sex = request.POST.get('sex')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("""
            SET search_path TO sijartagroupassignment;
            UPDATE "USER" SET name = %s, phonenum = %s, sex = %s, dob = %s, address = %s
            WHERE id = %s;
            """, [name, phone, sex, dob, address, user_id])

            if password:
                cursor.execute("""
                UPDATE "USER" SET pwd = %s WHERE id = %s;
                """, [make_password(password), user_id])

            if role == 'Worker':
                bank_name = request.POST.get('bank_name')
                acc_number = request.POST.get('acc_number')
                npwp = request.POST.get('npwp')
                pic_url = request.POST.get('pic_url')

                cursor.execute("""
                UPDATE WORKER SET bankname = %s, accnumber = %s, npwp = %s, picurl = %s 
                WHERE id = %s;
                """, [bank_name, acc_number, npwp, pic_url, user_id])

        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    with connection.cursor() as cursor:
        cursor.execute("""
        SET search_path TO sijartagroupassignment;
        SELECT * FROM "USER" WHERE id = %s;
        """, [user_id])
        user = cursor.fetchone()

        profile_data = {}
        
        if role == 'Worker':
            cursor.execute("""
            SELECT * FROM WORKER WHERE id = %s;
            """, [user_id])
            profile = cursor.fetchone()
            profile_data = {
                'bank_name': profile[1],
                'acc_number': profile[2],
                'npwp': profile[3],
                'pic_url': profile[4]
            }

    context = {
        'user': {
            'id': user[0],
            'name': user[1],
            'sex': user[2],
            'phone_num': user[3],
            'dob': user[5],
            'address': user[6]
        },
        'profile': profile_data,
        'role': role
    }
    return render(request, 'profile_update.html', context)

def homepage(request):
    return render(request, 'landingpage.html')
