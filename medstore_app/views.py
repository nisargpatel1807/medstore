from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction

from .models import User, Category, Medicine, Order, OrderItem, ContactMessage

ADMIN_EMAIL = "admin@medstore.com"


# -------------------------
# Helper / decorator
# -------------------------
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.COOKIES.get('admin_email') != ADMIN_EMAIL:
            return redirect('medstore_app:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# -------------------------
# Public pages / auth
# -------------------------
def show_home_page(request):
    products = Medicine.objects.all()
    user_email = request.COOKIES.get('user_email')
    user = User.objects.filter(email=user_email).first()
    return render(request, 'medstore_app/home.html', {'products': products, 'user': user})


def show_login_page(request):
    if request.method == "GET":
        if request.COOKIES.get('user_email'):
            return redirect('medstore_app:home')
        return render(request, 'medstore_app/login.html')
    return login(request)


def login(request):
    # optional debug prints (remove after testing)
    print("DEBUG: login called, method=", request.method)
    print("DEBUG POST:", dict(request.POST))

    identifier = request.POST.get('identifier')
    password = request.POST.get('password')

    if not identifier or not password:
        return render(request, 'medstore_app/login.html', {"error": "All fields are required"})

    user = User.objects.filter(email=identifier).first() \
           or User.objects.filter(username=identifier).first() \
           or User.objects.filter(mobile=identifier).first()

    if not user:
        return render(request, 'medstore_app/login.html', {"error": "User not found. Please signup."})

    if not check_password(password, user.password):
        return render(request, 'medstore_app/login.html', {"error": "Invalid login details"})

    # SUCCESS: set cookie and remove admin cookie (so header shows user-nav)
    response = redirect('medstore_app:home')
    response.set_cookie('user_email', user.email, max_age=7 * 24 * 60 * 60)
    response.delete_cookie('admin_email')
    messages.success(request, f"Welcome {user.username}!")
    return response


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
        return render(request, 'medstore_app/signup.html', {"error": "Username taken"})
    if User.objects.filter(mobile=mobile).exists():
        return render(request, 'medstore_app/signup.html', {"error": "Mobile already used"})

    hashed_password = make_password(password)
    user = User.objects.create(username=username, mobile=mobile, email=email, password=hashed_password)

    # auto-login after signup
    resp = redirect('medstore_app:home')
    resp.set_cookie('user_email', user.email, max_age=7*24*60*60)
    resp.delete_cookie('admin_email')
    messages.success(request, "Account created and logged in! Welcome.")
    return resp

from django.shortcuts import redirect
from django.contrib import messages

def logout_view(request):
    resp = redirect('medstore_app:home')
    resp.delete_cookie('user_email')
    messages.info(request, "You have been logged out.")
    return resp


def show_about_page(request):
    return render(request, 'medstore_app/about.html')


def show_contact_page(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_text = request.POST.get('message')
        if not (name and email and message_text):
            return render(request, 'medstore_app/contact.html', {"error": "Please fill all fields"})
        ContactMessage.objects.create(name=name, email=email, message=message_text)
        return render(request, 'medstore_app/contact.html', {"success": "Message sent successfully!"})
    return render(request, 'medstore_app/contact.html')


# -------------------------
# Admin auth + pages
# -------------------------
def admin_login_page(request):
    if request.method == "GET" and request.COOKIES.get('admin_email'):
        return redirect('medstore_app:admin_dashboard')
    if request.method == "GET":
        return render(request, 'medstore_app/admin_login.html')

    email = (request.POST.get('email') or "").strip()
    password = (request.POST.get('password') or "")

    if not email or not password:
        return render(request, 'medstore_app/admin_login.html', {'error': 'Please fill both fields.'})

    user = User.objects.filter(email=email).first()
    if not user or email != ADMIN_EMAIL or not check_password(password, user.password):
        return render(request, 'medstore_app/admin_login.html', {'error': 'Invalid admin login'})

    resp = redirect('medstore_app:admin_dashboard')
    resp.set_cookie('admin_email', user.email, max_age=7*24*60*60)
    resp.delete_cookie('user_email')
    return resp


def admin_logout(request):
    resp = redirect('medstore_app:admin_login')
    resp.delete_cookie('admin_email')
    return resp


@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_products = Medicine.objects.count()
    total_orders = Order.objects.count()
    # NOTE: if model uses 'date' instead of 'created_at', change below to '-date'
    recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]
    return render(request, 'medstore_app/admin_dashboard.html', {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'recent_messages': recent_messages
    })


@admin_required
def admin_view_messages(request):
    msgs = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'medstore_app/admin_view_messages.html', {'messages': msgs})


@admin_required
def admin_add_category(request):
    if request.method == "POST":
        name = (request.POST.get('name') or "").strip()
        if not name:
            return render(request, 'medstore_app/admin_add_category.html', {'error': 'Category name required'})
        Category.objects.create(name=name)
        return render(request, 'medstore_app/admin_add_category.html', {'success': 'Category added successfully'})
    return render(request, 'medstore_app/admin_add_category.html')


@admin_required
def admin_add_medicine(request):
    if request.method == "POST":
        name = (request.POST.get('name') or "").strip()
        price = request.POST.get('price') or "0"
        description = request.POST.get('description') or ""
        cat_id = request.POST.get('category_id') or None
        stock = request.POST.get('stock') or "0"
        try:
            price = float(price)
        except:
            price = 0.0
        try:
            stock = int(stock)
        except:
            stock = 0

        category_obj = None
        if cat_id:
            try:
                category_obj = Category.objects.get(id=int(cat_id))
            except (Category.DoesNotExist, ValueError):
                category_obj = None

        Medicine.objects.create(
            name=name,
            price=price,
            description=description,
            category=category_obj,
            stock=stock
        )
        return render(request, 'medstore_app/admin_add_medicine.html', {
            'success': 'Medicine added', 'categories': Category.objects.all()
        })
    return render(request, 'medstore_app/admin_add_medicine.html', {'categories': Category.objects.all()})


@admin_required
def admin_view_orders(request):
    try:
        orders = Order.objects.all().order_by('-created_at')
    except Exception:
        try:
            orders = Order.objects.all().order_by('-datetime')
        except Exception:
            orders = Order.objects.all().order_by('-id')

    return render(request, 'medstore_app/admin_view_orders.html', {
        'orders': orders
    })


@admin_required
def admin_view_orders(request):
    # duplicate safe guard — keep only one definition; if you see this twice remove one
    try:
        orders = Order.objects.all().order_by('-created_at')
    except Exception:
        orders = Order.objects.all().order_by('-id')
    return render(request, 'medstore_app/admin_view_orders.html', {'orders': orders})


def create_order(request, med_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for ordering.')
        return redirect('medstore_app:home')

    user_email = request.COOKIES.get('user_email')
    if not user_email:
        messages.error(request, 'Please login to place order.')
        return redirect('medstore_app:login')

    user = User.objects.filter(email=user_email).first()
    if not user:
        messages.error(request, 'User not found. Please login again.')
        return redirect('medstore_app:login')

    med = Medicine.objects.filter(id=med_id).first()
    if not med:
        messages.error(request, 'Medicine not found.')
        return redirect('medstore_app:home')

    try:
        qty = int(request.POST.get('quantity', '1'))
        if qty < 1:
            qty = 1
    except ValueError:
        qty = 1

    if med.stock is not None and med.stock < qty:
        messages.error(request, 'Not enough stock available.')
        return redirect('medstore_app:home')

    try:
        with transaction.atomic():
            order = Order.objects.create(user=user, total_amount=0.0, status='placed')
            item_price = med.price
            OrderItem.objects.create(order=order, medicine=med, quantity=qty, price=item_price)
            order.total_amount = item_price * qty
            order.save()
            if med.stock is not None:
                med.stock = max(0, med.stock - qty)
                med.save()
    except Exception:
        messages.error(request, 'Could not place order. Try again.')
        return redirect('medstore_app:home')

    messages.success(request, f'Order placed (ID: {order.id}). Admin will process it.')
    return redirect('medstore_app:home')
