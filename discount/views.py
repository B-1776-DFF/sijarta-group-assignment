from django.shortcuts import render

# Create your views here.
def discount_view(request):
    return render(request, 'discount.html')