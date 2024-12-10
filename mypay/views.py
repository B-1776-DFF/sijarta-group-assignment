from django.shortcuts import render, redirect
import json
from collections import Counter
from datetime import datetime
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from uuid import *

def mypay_view(request):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    #user_id = 'a322b805-43a8-48e2-901b-a0dda9b38924' # Sample user ID
    user_id = request.session.get('user_id') # Getting user's ID

    with connection.cursor() as cursor:
        # Getting user's name, phone number, and balance
        cursor.execute("""
            SELECT name, phonenum, mypaybalance 
            FROM sijartagroupassignment."USER" 
            WHERE id = %s
        """, [user_id])
        
        user_data = cursor.fetchone()
        if not user_data:
            return render(request, "mypay.html", {
                "user": {"name": "Guest", "phone": ""},
                "balance": 0,
                "transactions": [],
                "transaction_data_json": "{}"
            })

        # User's transaction history
        cursor.execute("""
            SELECT 
                tm.nominal,
                tm.date,
                tmc.name as category
            FROM sijartagroupassignment.tr_mypay tm
            JOIN sijartagroupassignment.tr_mypay_category tmc 
                ON tm.categoryid = tmc.id
            WHERE tm.userid = %s
            ORDER BY tm.date DESC, tm.id DESC
        """, [user_id])
        
        transactions = []
        for row in cursor.fetchall():
            amount = float(row[0])
            transactions.append({
                "amount": f"{abs(amount):,.2f}",
                "date": row[1].strftime("%Y-%m-%d"),
                "category": row[2]
            })

        context = {
            "user": {
                "name": user_data[0],
                "phone": user_data[1]
            },
            "balance": float(user_data[2]) if user_data[2] else 0,
            "transactions": transactions,
            "transaction_data_json": json.dumps(
                dict(Counter(t["category"] for t in transactions))
            )
        }
        
        return render(request, "mypay.html", context)

@csrf_exempt
def mypay_transactions(request):
    uuid = request.session.get('user_id')
    if not uuid:
        return redirect('landingpage')
    
    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({"success": False, "message": "User not logged in"}, status=403)

        data = json.loads(request.body.decode("utf-8"))
        transaction_type = data.get("transaction_type")

        try:
            with connection.cursor() as cursor:
                # State 1: TopUp MyPay
                if transaction_type == "Top-up":
                    amount = float(data.get("amount", 0))
                    if amount <= 0:
                        return JsonResponse({"success": False, "message": "Invalid top-up amount"}, status=400)

                    # Update user balance
                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance + %s
                        WHERE id = %s
                    """, [amount, user_id])

                    # Record transaction
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (id, userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Top-Up'))
                    """, [str(uuid4()), user_id, amount, datetime.now()])

                    return JsonResponse({"success": True, "message": "Top-up successful"})

                # State 2: Service Payment
                elif transaction_type == "Payment":
                    order_id = data.get("order_id")
                    if not order_id:
                        return JsonResponse({"success": False, "message": "Order ID required"}, status=400)

                    # Get order details
                    cursor.execute("""
                        SELECT tso.totalprice, tso.id 
                        FROM sijartagroupassignment.tr_service_order tso
                        JOIN sijartagroupassignment.tr_order_status tos ON tso.id = tos.servicetrid
                        JOIN sijartagroupassignment.order_status os ON tos.statusid = os.id
                        WHERE tso.id = %s AND tso.customerid = %s
                        AND os.status = 'Payment Pending'
                    """, [order_id, user_id])
                    
                    order = cursor.fetchone()
                    if not order:
                        return JsonResponse({"success": False, "message": "Invalid or already paid order"}, status=404)

                    price = float(order[0])

                    # Check and update balance
                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                        RETURNING mypaybalance
                    """, [price, user_id, price])

                    if cursor.rowcount == 0:
                        return JsonResponse({"success": False, "message": "Insufficient balance"}, status=400)

                    # Record payment transaction
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (id, userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Payment'))
                    """, [str(uuid4()), user_id, -price, datetime.now()])

                    # Update order status to Processing
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_order_status (servicetrid, statusid, date)
                        VALUES (%s, (SELECT id FROM sijartagroupassignment.order_status WHERE status = 'Processing'), %s)
                    """, [order_id, datetime.now()])

                    return JsonResponse({"success": True, "message": "Payment successful"})

                elif transaction_type == "Transfer":
                    recipient_phone = data.get("recipient_phone")
                    amount = float(data.get("amount", 0))

                    if not recipient_phone or amount <= 0:
                        return JsonResponse({"success": False, "message": "Invalid transfer details"}, status=400)

                    # Get recipient ID
                    cursor.execute("""
                        SELECT id FROM sijartagroupassignment."USER"
                        WHERE phonenum = %s
                    """, [recipient_phone])
                    
                    recipient = cursor.fetchone()
                    if not recipient:
                        return JsonResponse({"success": False, "message": "Recipient not found"}, status=404)

                    recipient_id = recipient[0]

                    # Deduct from sender
                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                    """, [amount, user_id, amount])

                    if cursor.rowcount == 0:
                        return JsonResponse({"success": False, "message": "Insufficient balance"}, status=400)

                    # Add to recipient
                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance + %s
                        WHERE id = %s
                    """, [amount, recipient_id])

                    # Record sender transaction
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (id, userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Transfer'))
                    """, [str(uuid4()), user_id, -amount, datetime.now()])

                    # Record recipient transaction
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (id, userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Received Transfer'))
                    """, [str(uuid4()), recipient_id, amount, datetime.now()])

                    return JsonResponse({"success": True, "message": "Transfer successful"})
                
                elif transaction_type == "Withdrawal":
                    bank_name = data.get("bank_name")
                    account_number = data.get("account_number")
                    amount = float(data.get("amount", 0))
                
                    if not bank_name or not account_number or amount <= 0:
                        return JsonResponse({
                            "success": False, 
                            "message": "Invalid withdrawal details"
                        }, status=400)
                
                    # Check and update balance
                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                        RETURNING mypaybalance
                    """, [amount, user_id, amount])
                
                    if cursor.rowcount == 0:
                        return JsonResponse({
                            "success": False, 
                            "message": "Insufficient balance"
                        }, status=400)
                
                    # Record withdrawal transaction
                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (id, userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Withdrawal'))
                    """, [str(uuid4()), user_id, -amount, datetime.now()])
                
                    return JsonResponse({
                        "success": True, 
                        "message": f"Successfully withdrawn {amount:,.2f} to {bank_name} account ending in {account_number[-4:]}"
                    })

                # Return error for invalid transaction type
                else:
                    return JsonResponse({"success": False, "message": "Invalid transaction type"}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)