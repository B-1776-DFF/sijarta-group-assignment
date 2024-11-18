from django.shortcuts import render, get_object_or_404
from .models import Category, Subcategory, Worker, Testimonial, ServiceSession, Booking
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse



# Homepage
def homepage(request):
    # Check if any categories exist
    categories = Category.objects.prefetch_related('subcategories').all()
    if not categories.exists():
        # Create sample categories
        category1, _ = Category.objects.get_or_create(name="Hair & Beauty")
        category2, _ = Category.objects.get_or_create(name="Health & Wellness")

        # Create sample subcategories for each category
        Subcategory.objects.get_or_create(
            name="Haircut Services",
            description="Professional haircut services for men, women, and children.",
            category=category1,
        )
        Subcategory.objects.get_or_create(
            name="Spa & Relaxation",
            description="Luxury spa treatments to help you unwind and relax.",
            category=category2,
        )
        Subcategory.objects.get_or_create(
            name="Facial Treatments",
            description="Revitalize your skin with our advanced facial treatments.",
            category=category1,
        )
        Subcategory.objects.get_or_create(
            name="Massage Therapy",
            description="Relieve stress and tension with our expert massage therapy.",
            category=category2,
        )

        # Re-fetch categories after creation
        categories = Category.objects.prefetch_related('subcategories').all()

    # Render the homepage template with the categories and subcategories
    return render(request, 'homepage.html', {'categories': categories})



# Subcategory User Page
def subcategory_user_view(request, subcategory_id):
    # Fetch or create a Subcategory for demonstration
    subcategory, created = Subcategory.objects.get_or_create(
        id=subcategory_id,
        defaults={
            'name': 'Haircut Services',
            'description': 'Professional haircut services for men, women, and children.',
        }
    )

    # Create sample workers if not present
    workers = subcategory.workers.all()
    if not workers.exists():
        # Create sample users
        user1, _ = User.objects.get_or_create(username="john_doe", defaults={'first_name': 'John', 'last_name': 'Doe'})
        user2, _ = User.objects.get_or_create(username="jane_smith", defaults={'first_name': 'Jane', 'last_name': 'Smith'})

        # Create workers and associate them with the subcategory
        worker1, _ = Worker.objects.get_or_create(user=user1)
        worker2, _ = Worker.objects.get_or_create(user=user2)
        worker1.subcategories.add(subcategory)
        worker2.subcategories.add(subcategory)

        workers = subcategory.workers.all()

    # Create sample service sessions if not present
    service_sessions = subcategory.service_sessions.all()
    if not service_sessions.exists():
        ServiceSession.objects.get_or_create(subcategory=subcategory, name="Basic Haircut", price=20)
        ServiceSession.objects.get_or_create(subcategory=subcategory, name="Haircut with Styling", price=35)
        service_sessions = subcategory.service_sessions.all()

    # Create sample testimonials if not present
    testimonials = subcategory.testimonials.all()
    if not testimonials.exists():
        Testimonial.objects.get_or_create(
            subcategory=subcategory,
            user=user1,
            feedback="Great haircut! I love the new style."
        )
        Testimonial.objects.get_or_create(
            subcategory=subcategory,
            user=user2,
            feedback="Very professional service!"
        )
        testimonials = subcategory.testimonials.all()

    # Pass data to the template
    return render(request, 'subcategory_user.html', {
        'subcategory': subcategory,
        'workers': workers,
        'testimonials': testimonials,
        'service_sessions': service_sessions,
    })



# Subcategory Worker Page

def subcategory_worker_view(request, subcategory_id):
    # Mock Subcategory data
    subcategory = {
        "id": subcategory_id,
        "name": "Photography Services",
        "description": "Professional photography for events and portraits.",
        "category": {"id": 3, "name": "Creative Services"},
    }

    # Mock worker data
    workers = [
        {"id": 1, "name": "Alice Smith"},
        {"id": 2, "name": "Bob Johnson"},
        {"id": 3, "name": "Charlie Brown"},
        {"id": 4, "name": "Diana Prince"},
    ]

    # Mock service sessions data
    service_sessions = [
        {"id": 1, "name": "Wedding Photoshoot", "price": 500.00},
        {"id": 2, "name": "Portrait Session", "price": 150.00},
    ]

    # Mock testimonial data
    testimonials = [
        {
            "user": {"id": 1, "username": "john_doe"},
            "feedback": "Excellent service! Highly recommended.",
            "rate": 5,
            "created_at": "2024-01-01",
        },
        {
            "user": {"id": 2, "username": "jane_doe"},
            "feedback": "Very professional and timely!",
            "rate": 4,
            "created_at": "2024-01-15",
        },
    ]

    # Mock whether the current user is joined as a worker
    is_worker_joined = False  # Change to True to simulate the joined state

    # Pass the mock data to the template
    return render(request, 'subcategory_worker.html', {
        'subcategory': subcategory,
        'workers': workers,
        'testimonials': testimonials,
        'service_sessions': service_sessions,
        'is_worker_joined': is_worker_joined,
    })

def subcategory_worker_view_json(request, subcategory_id):
    # Mock Subcategory data
    subcategory = {
        "id": subcategory_id,
        "name": "Photography Services",
        "description": "Professional photography for events and portraits.",
        "category": {"id": 3, "name": "Creative Services"},
    }

    # Mock worker data
    workers = [
        {"id": 1, "name": "Alice Smith"},
        {"id": 2, "name": "Bob Johnson"},
        {"id": 3, "name": "Charlie Brown"},
        {"id": 4, "name": "Diana Prince"},
    ]

    # Mock service sessions data
    service_sessions = [
        {"id": 1, "name": "Wedding Photoshoot", "price": 500.00},
        {"id": 2, "name": "Portrait Session", "price": 150.00},
    ]

    # Mock testimonial data
    testimonials = [
        {
            "user": {"id": 1, "username": "john_doe"},
            "feedback": "Excellent service! Highly recommended.",
            "rate": 5,
            "created_at": "2024-01-01",
        },
        {
            "user": {"id": 2, "username": "jane_doe"},
            "feedback": "Very professional and timely!",
            "rate": 4,
            "created_at": "2024-01-15",
        },
    ]

    # Mock whether the current user is joined as a worker
    is_worker_joined = False  # Change to True to simulate the joined state

    # Structure the JSON response
    response_data = {
        "subcategory": subcategory,
        "workers": workers,
        "testimonials": testimonials,
        "service_sessions": service_sessions,
        "is_worker_joined": is_worker_joined,
    }

    # Return the response as JSON
    return JsonResponse(response_data)    

# Join Subcategory (for Workers)
@login_required
def join_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    worker, created = Worker.objects.get_or_create(user=request.user)
    worker.subcategories.add(subcategory)
    return redirect('subcategory_worker', subcategory_id=subcategory.id)


def book_session(request, session_id):
    if request.method == 'POST':
        # Assuming a logged-in user (add authentication checks here)
        user = request.user
        try:
            session = ServiceSession.objects.get(id=session_id)
            # Add logic to book the session (e.g., create a booking record)
            # Example:
            # Booking.objects.create(user=user, session=session)
            return JsonResponse({'success': True, 'message': 'Booking successful!'})
        except ServiceSession.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Service session not found.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})
