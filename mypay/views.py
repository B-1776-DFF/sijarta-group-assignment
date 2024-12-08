from django.shortcuts import render, redirect
import json
from collections import Counter
from datetime import datetime
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def mypay_view(request):
    user_id = '26b7d02c-6d45-4630-a848-e8a84494eeeb' # Sample user ID
    #user_id = request.session.get('user_id') # Getting user's ID

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
            ORDER BY tm.date DESC
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
            "balance": float(user_data[2]),
            "transactions": transactions,
            "transaction_data_json": json.dumps(
                dict(Counter(t["category"] for t in transactions))
            )
        }
        
        return render(request, "mypay.html", context)

@csrf_exempt
def mypay_transactions(request):
    if request.method == "POST":
        user_id = 'dd426b67-a25e-4378-b493-6e62c70a0a8d' # Sample user ID
        #user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({"success": False, "message": "User not logged in"}, status=403)

        data = json.loads(request.body.decode("utf-8"))
        transaction_type = data.get("transaction_type")

        try:
            with connection.cursor() as cursor:
                # State 1: TopUp MyPay
                if transaction_type == "topup":
                    amount = float(data.get("amount", 0))
                    if amount <= 0:
                        return JsonResponse({"success": False, "message": "Invalid top-up amount"}, status=400)

                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance + %s
                        WHERE id = %s
                    """, [amount, user_id])

                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Top-Up'))
                    """, [user_id, amount, datetime.now()])

                    return JsonResponse({"success": True, "message": "Top-up successful"})

                # State 2: Service Payment
                elif transaction_type == "service_payment":
                    service_id = data.get("service_id")
                    if not service_id:
                        return JsonResponse({"success": False, "message": "Service ID required"}, status=400)

                    cursor.execute("""
                        SELECT price FROM sijartagroupassignment.services
                        WHERE id = %s AND userid = %s
                    """, [service_id, user_id])
                    service = cursor.fetchone()
                    if not service:
                        return JsonResponse({"success": False, "message": "Service not found"}, status=404)

                    price = float(service[0])

                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                    """, [price, user_id, price])

                    if cursor.rowcount == 0:
                        return JsonResponse({"success": False, "message": "Insufficient balance"}, status=400)

                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Service Payment'))
                    """, [user_id, -price, datetime.now()])

                    return JsonResponse({"success": True, "message": "Service payment successful"})

                # State 3: Transfer MyPay
                elif transaction_type == "transfer":
                    recipient_phone = data.get("recipient_phone")
                    amount = float(data.get("amount", 0))

                    if amount <= 0:
                        return JsonResponse({"success": False, "message": "Invalid transfer amount"}, status=400)

                    cursor.execute("""
                        SELECT id FROM sijartagroupassignment."USER" WHERE phonenum = %s
                    """, [recipient_phone])
                    recipient = cursor.fetchone()

                    if not recipient:
                        return JsonResponse({"success": False, "message": "Recipient not found"}, status=404)

                    recipient_id = recipient[0]

                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                    """, [amount, user_id, amount])

                    if cursor.rowcount == 0:
                        return JsonResponse({"success": False, "message": "Insufficient balance"}, status=400)

                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance + %s
                        WHERE id = %s
                    """, [amount, recipient_id])

                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Transfer'))
                    """, [user_id, -amount, datetime.now()])

                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (userid, nominal, date, categoryid)
                        VALUES (%s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Received Transfer'))
                    """, [recipient_id, amount, datetime.now()])

                    return JsonResponse({"success": True, "message": "Transfer successful"})

                # State 4: Withdrawal
                elif transaction_type == "withdrawal":
                    bank_name = data.get("bank_name")
                    account_number = data.get("account_number")
                    amount = float(data.get("amount", 0))

                    if not bank_name or not account_number or amount <= 0:
                        return JsonResponse({"success": False, "message": "Invalid withdrawal details"}, status=400)

                    cursor.execute("""
                        UPDATE sijartagroupassignment."USER"
                        SET mypaybalance = mypaybalance - %s
                        WHERE id = %s AND mypaybalance >= %s
                    """, [amount, user_id, amount])

                    if cursor.rowcount == 0:
                        return JsonResponse({"success": False, "message": "Insufficient balance"}, status=400)

                    cursor.execute("""
                        INSERT INTO sijartagroupassignment.tr_mypay (userid, nominal, date, categoryid, details)
                        VALUES (%s, %s, %s, (SELECT id FROM sijartagroupassignment.tr_mypay_category WHERE name = 'Withdrawal'), %s)
                    """, [user_id, -amount, datetime.now(), f"{bank_name} - {account_number}"])

                    return JsonResponse({"success": True, "message": "Withdrawal successful"})

                else:
                    return JsonResponse({"success": False, "message": "Invalid transaction type"}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)
