from django.urls import path
from . import views

app_name = 'medstore_app'

urlpatterns = [
    path('', views.show_home_page, name='home'),
    path('login/', views.show_login_page, name='login'),
    path('signup/', views.show_signup_page, name='signup'),
    path('about/', views.show_about_page, name='about'),
    path('contact/', views.show_contact_page, name='contact'),
   # new (preferred)
path('admin-panel/login/', views.admin_login_page, name='admin_login'),
path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
path('admin-panel/add-category/', views.admin_add_category, name='admin_add_category'),
path('admin-panel/add-medicine/', views.admin_add_medicine, name='admin_add_medicine'),
path('admin-panel/messages/', views.admin_view_messages, name='admin_messages'),
path('admin-panel/orders/', views.admin_view_orders, name='admin_orders'),
path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
 path('order/<int:med_id>/', views.create_order, name='create_order'),

]

