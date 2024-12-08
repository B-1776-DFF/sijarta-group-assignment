from django.shortcuts import render, redirect
from django.db import connection
from datetime import date
from django.http import JsonResponse


def discount_view(request):
    # Check if user is logged in
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('login')

    vouchers = []
    promos = []
    payment_methods = []

    with connection.cursor() as cursor:
        # Fetch vouchers
        cursor.execute("""
        SET search_path TO sijartagroupassignment;
        SELECT 
            d.code, 
            d.discount, 
            d.mintrorder, 
            v.nmbdayvalid, 
            v.userquota, 
            v.price
        FROM discount d
        INNER JOIN voucher v ON d.code = v.code;
        """)
        vouchers = cursor.fetchall()
        
        # Fetch non-expired promos
        cursor.execute("""
        SELECT 
            d.code, 
            d.discount, 
            p.offerenddate
        FROM discount d
        INNER JOIN promo p ON d.code = p.code
        WHERE p.offerenddate >= %s;
        """, [date.today()])
        promos = cursor.fetchall()

        # Fetch available payment methods
        cursor.execute("""
        SELECT name FROM payment_method;
        """)
        payment_methods = cursor.fetchall()

    # Prepare context data for rendering
    context = {
        'vouchers': vouchers,
        'promos': promos,
        'payment_methods': payment_methods,  # Pass payment methods to the context
    }

    return render(request, 'discount.html', context)

def get_user_balance(request):
    user_phone_num = request.session.get('user_phone_num')
    
    if user_phone_num:
        with connection.cursor() as cursor:
            cursor.execute("""
            SET search_path TO sijartagroupassignment;
            SELECT mypaybalance FROM "USER" WHERE phonenum = %s;
            """, [user_phone_num])  # Use parameterized query to prevent SQL injection
            result = cursor.fetchone()
            if result:
                balance = result[0]
                print(f"User's MyPay Balance: {balance}")  # Log balance to terminal
                return JsonResponse({'balance': balance})
            else:
                print(f"No user found with phone number: {user_phone_num}")
                return JsonResponse({'balance': 0})  # In case no balance is found
    else:
        print("No phone number found in session")
        return JsonResponse({'balance': 0})
    
