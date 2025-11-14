from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

from .models import User, Medicine, ContactMessage


def show_home_page(request):
    # if request.COOKIES.get('user_email') is None:
    #     return redirect('/login')

    products = Medicine.objects.all()
    user_email = request.COOKIES.get('user_email')
    user = User.objects.filter(email=user_email).first()
    return render(request, 'medstore_app/home.html', {'products': products, 'user': user})


def show_login_page(request):
    if request.method == "GET":
        if request.COOKIES.get('user_email'):
            return redirect('/')
        return render(request, 'medstore_app/login.html')

    return login(request)


def login(request):
    identifier = request.POST.get('identifier')
    password = request.POST.get('password')

    if not identifier or not password:
        return render(request, 'medstore_app/login.html', {"error": "All fields are required"})

    user = User.objects.filter(email=identifier).first()
    if not user:
        user = User.objects.filter(username=identifier).first()
    if not user:
        user = User.objects.filter(mobile=identifier).first()

    if not user or not check_password(password, user.password):
        return render(request, 'medstore_app/login.html', {"error": "Invalid login details"})

    response = redirect('/')
    response.set_cookie('user_email', user.email, max_age=7 * 24 * 60 * 60)
    messages.success(request, f"Welcome {user.username}!")
    return response



def show_signup_page(request):
    if request.method == "GET":
        if request.COOKIES.get('user_email'):
            return redirect('/')
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
    User.objects.create(username=username, mobile=mobile, email=email, password=hashed_password)
    return render(request, 'medstore_app/signup.html', {"success": "Account created! You can login now."})



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
