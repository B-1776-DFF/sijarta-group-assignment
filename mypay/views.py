from django.shortcuts import render
import json
from collections import Counter
from datetime import datetime

# MyPay Dashboard View
def mypay_view(request):
    # Sample data to display on the template
    user = [
        {"name": "Andriyo Averill", "phone": "0812 3456 7890"},
    ]
    balance = 500000.00  # Example balance
    transactions = [
        {"amount": "+100.000,00", "date": "2024-11-10", "category": "Top-Up"},
        {"amount": "+50.000,00", "date": "2024-11-20", "category": "Top-Up"},
        {"amount": "+150.000,00", "date": "2024-11-15", "category": "Top-Up"},
        {"amount": "-100.000,00", "date": "2024-11-09", "category": "Transfer"},
        {"amount": "-50.000,00", "date": "2024-11-11", "category": "Transfer"},
        {"amount": "-100.000,00", "date": "2024-11-08", "category": "Withdrawal"},
    ]
    
    # Sort transactions by date in descending order
    transactions = sorted(transactions, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
    
    # Count the number of each transaction type
    transaction_counts = Counter([transaction["category"] for transaction in transactions])
    
    # Convert the counts to JSON format
    transaction_data_json = json.dumps(transaction_counts)
    
    # Pass data to the template
    context = {
        "user": user[0],
        "balance": balance,
        "transactions": transactions,
        "transaction_data_json": transaction_data_json,
    }
    return render(request, "mypay.html", context)