from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction

from .models import User, Category, Medicine, Order, OrderItem, ContactMessage

ADMIN_EMAIL = "admin@medstore.com"

# =========================
# Admin decorator
# =========================
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.COOKIES.get('admin_email') != ADMIN_EMAIL:
            return redirect('medstore_app:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# =========================
# User Pages
# =========================
def show_home_page(request):
    products = Medicine.objects.all()
    user_email = request.COOKIES.get('user_email')
    user = User.objects.filter(email=user_email).first()

    orders = []
    if user:
        orders = Order.objects.filter(user=user).order_by('-id')

    return render(request, 'medstore_app/home.html', {
        'products': products,
        'user': user,
        'orders': orders
    })


def show_login_page(request):
    if request.method == "GET":
        if request.COOKIES.get('user_email'):
            return redirect('medstore_app:home')
        return render(request, 'medstore_app/login.html')
    return login(request)


def login(request):
    identifier = request.POST.get('identifier')
    password = request.POST.get('password')

    if not identifier or not password:
        return render(request, 'medstore_app/login.html', {"error": "All fields are required"})

    user = (
        User.objects.filter(email=identifier).first()
        or User.objects.filter(username=identifier).first()
        or User.objects.filter(mobile=identifier).first()
    )

    if not user or not check_password(password, user.password):
        return render(request, 'medstore_app/login.html', {"error": "Invalid login details"})

    resp = redirect('medstore_app:home')
    resp.set_cookie('user_email', user.email, max_age=7 * 24 * 60 * 60)
    resp.delete_cookie('admin_email')
    messages.success(request, f"Welcome {user.username}!")
    return resp


def show_signup_page(request):
    if request.method == "GET" and request.COOKIES.get('user_email'):
        return redirect('medstore_app:home')
    if request.method == "GET":
        return render(request, 'medstore_app/signup.html')
    return signup(request)


def signup(request):
    username = request.POST.get('username')
    mobile = request.POST.get('mobile')
    email = request.POST.get('email')
    password = request.POST.get('password')
    confirm = request.POST.get('confirm')

    if not (username and mobile and email and password and confirm):
        return render(request, 'medstore_app/signup.html', {"error": "All fields are required"})
    if password != confirm:
        return render(request, 'medstore_app/signup.html', {"error": "Passwords do not match"})
    if User.objects.filter(email=email).exists():
        return render(request, 'medstore_app/signup.html', {"error": "Email already exists"})
    if User.objects.filter(username=username).exists():
        return render(request, 'medstore_app/signup.html', {"error": "Username already taken"})
    if User.objects.filter(mobile=mobile).exists():
        return render(request, 'medstore_app/signup.html', {"error": "Mobile already used"})

    user = User.objects.create(
        username=username,
        mobile=mobile,
        email=email,
        password=make_password(password)
    )

    resp = redirect('medstore_app:home')
    resp.set_cookie('user_email', user.email, max_age=7 * 24 * 60 * 60)
    messages.success(request, "Account created successfully!")
    return resp


def logout_view(request):
    resp = redirect('medstore_app:home')
    resp.delete_cookie('user_email')
    messages.info(request, "Logged out successfully.")
    return resp


def show_about_page(request):
    return render(request, 'medstore_app/about.html')


def show_contact_page(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        msg = request.POST.get('message')

        if not (name and email and msg):
            return render(request, 'medstore_app/contact.html', {"error": "All fields required"})

        ContactMessage.objects.create(name=name, email=email, message=msg)
        return render(request, 'medstore_app/contact.html', {"success": "Message sent!"})

    return render(request, 'medstore_app/contact.html')


# =========================
# Admin Auth
# =========================
def admin_login_page(request):
    if request.method == "GET":
        if request.COOKIES.get('admin_email'):
            return redirect('medstore_app:admin_dashboard')
        return render(request, 'medstore_app/admin_login.html')

    email = request.POST.get('email')
    password = request.POST.get('password')

    user = User.objects.filter(email=email).first()

    if not user or email != ADMIN_EMAIL or not check_password(password, user.password):
        return render(request, 'medstore_app/admin_login.html', {"error": "Invalid admin login"})

    resp = redirect('medstore_app:admin_dashboard')
    resp.set_cookie('admin_email', user.email, max_age=7 * 24 * 60 * 60)
    resp.delete_cookie('user_email')
    return resp


def admin_logout(request):
    resp = redirect('medstore_app:admin_login')
    resp.delete_cookie('admin_email')
    return resp


# =========================
# Admin Pages
# =========================
@admin_required
def admin_dashboard(request):
    return render(request, 'medstore_app/admin_dashboard.html', {
        'total_users': User.objects.count(),
        'total_products': Medicine.objects.count(),
        'total_orders': Order.objects.count(),
    })


@admin_required
def admin_add_category(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if not name:
            return render(request, 'medstore_app/admin_add_category.html', {"error": "Name required"})
        Category.objects.create(name=name)
        return render(request, 'medstore_app/admin_add_category.html', {"success": "Category added"})
    return render(request, 'medstore_app/admin_add_category.html')


@admin_required
def admin_add_medicine(request):
    if request.method == "POST":
        Medicine.objects.create(
            name=request.POST.get('name'),
            price=float(request.POST.get('price') or 0),
            stock=int(request.POST.get('stock') or 0),
            category_id=request.POST.get('category_id') or None
        )
        return render(request, 'medstore_app/admin_add_medicine.html', {
            "success": "Medicine added",
            "categories": Category.objects.all()
        })

    return render(request, 'medstore_app/admin_add_medicine.html', {
        "categories": Category.objects.all()
    })


@admin_required
def admin_view_orders(request):
    orders = Order.objects.all().order_by('-id')
    return render(request, 'medstore_app/admin_orders.html', {'orders': orders})


@admin_required
def admin_accept_order(request, order_id):
    order = Order.objects.filter(id=order_id).first()
    if order:
        order.status = "ACCEPTED"
        order.save()
    return redirect('medstore_app:admin_orders')


@admin_required
def admin_deliver_order(request, order_id):
    order = Order.objects.filter(id=order_id).first()
    if order:
        order.status = "DELIVERED"
        order.save()
    return redirect('medstore_app:admin_orders')


# =========================
# User Order
# =========================
def create_order(request, med_id):
    if request.method != 'POST':
        return redirect('medstore_app:home')

    user_email = request.COOKIES.get('user_email')
    user = User.objects.filter(email=user_email).first()

    if not user:
        messages.error(request, "Please login first")
        return redirect('medstore_app:login')

    med = Medicine.objects.filter(id=med_id).first()
    if not med:
        messages.error(request, "Medicine not found")
        return redirect('medstore_app:home')

    qty = int(request.POST.get('quantity', 1))
    if med.stock < qty:
        messages.error(request, "Not enough stock")
        return redirect('medstore_app:home')

    with transaction.atomic():
        order = Order.objects.create(user=user, total_amount=med.price * qty, status="PLACED")
        OrderItem.objects.create(order=order, medicine=med, quantity=qty, price=med.price)
        med.stock -= qty
        med.save()

    messages.success(request, f"Order placed successfully (ID {order.id})")
    return redirect('medstore_app:home')
@admin_required
def admin_view_messages(request):
    messages_list = ContactMessage.objects.all().order_by('-id')
    return render(request, 'medstore_app/admin_view_messages.html', {
        'messages': messages_list
    })
