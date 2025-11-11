from django.shortcuts import render, redirect
from django.contrib import messages

# simple list to hold temporary user data
users_data = []

def home(request):
    # sample products list (for now static)
    products = [
        {"name": "Paracetamol 500mg", "price": "₹25", "desc": "Pain relief tablet"},
        {"name": "Vitamin C Tablets", "price": "₹120", "desc": "Boosts immunity"},
        {"name": "Cough Syrup", "price": "₹90", "desc": "Soothes dry cough"},
        {"name": "Hand Sanitizer 100ml", "price": "₹45", "desc": "Kills 99.9% germs"},
    ]
    return render(request, 'medstore_app/home.html', {'products': products})


def about(request):
    return render(request, 'medstore_app/about.html')


def contact(request):
    return render(request, 'medstore_app/contact.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        if not username or not mobile or not email or not password or not confirm:
            messages.error(request, "Please fill all fields.")
            return render(request, 'medstore_app/signup.html')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'medstore_app/signup.html')

        for u in users_data:
            if u['username'] == username or u['mobile'] == mobile or u['email'] == email:
                messages.error(request, "User already exists.")
                return render(request, 'medstore_app/signup.html')

        users_data.append({
            "username": username,
            "mobile": mobile,
            "email": email,
            "password": password
        })
        messages.success(request, "Account created successfully! You can now login.")
        return redirect('medstore_app:login')

    return render(request, 'medstore_app/signup.html')


def login_view(request):
    if request.method == 'POST':
        username_or_mobile = request.POST.get('username_or_mobile')
        password = request.POST.get('password')

        for u in users_data:
            if (u['username'] == username_or_mobile or u['mobile'] == username_or_mobile) and u['password'] == password:
                messages.success(request, f"Welcome {u['username']}! Logged in successfully.")
                return redirect('medstore_app:home')

        messages.error(request, "Invalid username/mobile or password.")
        return render(request, 'medstore_app/login.html')

    return render(request, 'medstore_app/login.html')


def logout_view(request):
    messages.info(request, "You have been logged out.")
    return redirect('medstore_app:home')
