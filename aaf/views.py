from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Customer, Worker

def login_view(request):
    if request.method == 'POST':
        phone = request.POST['phone']
        password = request.POST['password']
        try:
            user = User.objects.get(phone_num=phone)
            if check_password(password, user.pwd):
                request.session['user_id'] = str(user.id)
                response = redirect('profile')
                if Worker.objects.filter(id=user.id).exists():
                    response.set_cookie('user_role', 'Worker')
                    print("User role set to Worker")
                elif Customer.objects.filter(id=user.id).exists():
                    response.set_cookie('user_role', 'Customer')
                    print("User role set to Customer")
                return response
            else:
                messages.error(request, "Invalid phone number or password.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, 'login.html')



def logout_view(request):
    # Clear the session and cookies
    response = redirect('login')
    request.session.flush()
    response.delete_cookie('user_role')
    return response

def register_user_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        password = make_password(request.POST['password'])
        sex = request.POST['sex']
        phone = request.POST['phone']
        dob = request.POST['dob']
        address = request.POST['address']

        # Create User
        user = User.objects.create(
            name=name, pwd=password, sex=sex, phone_num=phone, dob=dob, address=address
        )

        # Create Customer
        Customer.objects.create(id=user)

        messages.success(request, "User registration successful!")
        return redirect('login')

    return render(request, 'register_user.html')


def register_worker_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        password = make_password(request.POST['password'])
        sex = request.POST['sex']
        phone = request.POST['phone']
        dob = request.POST['dob']
        address = request.POST['address']
        bank_name = request.POST['bank_name']
        acc_number = request.POST['acc_number']
        npwp = request.POST['npwp']
        pic_url = request.POST['pic_url']

        # Create User
        user = User.objects.create(
            name=name, pwd=password, sex=sex, phone_num=phone, dob=dob, address=address
        )

        # Create Worker
        Worker.objects.create(
            id=user, bank_name=bank_name, acc_number=acc_number, npwp=npwp, pic_url=pic_url
        )

        messages.success(request, "Worker registration successful!")
        return redirect('login')

    return render(request, 'register_worker.html')

def profile_update_view(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.name = request.POST['name']
        user.phone_num = request.POST['phone']
        user.address = request.POST['address']
        if hasattr(user, 'worker'):
            worker = user.worker
            worker.bank_name = request.POST['bank_name']
            worker.acc_number = request.POST['acc_number']
            worker.save()
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    context = {'user': user}
    return render(request, 'profile_update.html', context)

def register_view(request):
    return render(request, 'register.html')

def profile_view(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)
    role = request.COOKIES.get('user_role')
    print(f"Role retrieved from cookies: {role}")

    context = {'user': user, 'role': role}
    if role == "Customer":
        context['profile'] = get_object_or_404(Customer, id=user_id)
    elif role == "Worker":
        context['profile'] = get_object_or_404(Worker, id=user_id)

    return render(request, 'profile.html', context)




def profile_update_view(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)
    role = request.session.get('user_role')

    if request.method == 'POST':
        user.name = request.POST['name']
        user.phone_num = request.POST['phone']
        user.sex = request.POST['sex']
        user.dob = request.POST['dob']
        user.address = request.POST['address']
        if password := request.POST.get('password'):
            user.pwd = make_password(password)

        if role == "Worker":
            worker = get_object_or_404(Worker, id=user_id)
            worker.bank_name = request.POST['bank_name']
            worker.acc_number = request.POST['acc_number']
            worker.npwp = request.POST['npwp']
            worker.pic_url = request.POST['pic_url']
            worker.save()

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    context = {'user': user, 'role': role}
    if role == "Worker":
        context['profile'] = get_object_or_404(Worker, id=user_id)

    return render(request, 'profile_update.html', context)

