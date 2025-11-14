from django.urls import path
from . import views

app_name = 'medstore_app'

urlpatterns = [
    path('', views.show_home_page, name='home'),
    path('login/', views.show_login_page, name='login'),
    path('signup/', views.show_signup_page, name='signup'),
    path('about/', views.show_about_page, name='about'),
    path('contact/', views.show_contact_page, name='contact'),
]

