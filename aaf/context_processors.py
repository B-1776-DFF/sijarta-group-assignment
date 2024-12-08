from django.db import connection

def user_context(request):
    user_phone_num = request.session.get('user_phone_num')
    name = None
    if user_phone_num:
        with connection.cursor() as cursor:
            cursor.execute(rf"""
            SET search_path TO sijartagroupassignment;
            SELECT name FROM "USER" WHERE phonenum = '{user_phone_num}';
            """)
            temp = cursor.fetchone()
            if temp:
                name = temp[0]
    role = request.session.get('user_role')
    print(f"User: {name}, Role: {role}")
    return {
        'user': name,
        'role': role,
    }