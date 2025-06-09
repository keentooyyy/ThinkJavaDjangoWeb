from django.urls import path

from StudentManagementSystem.views.admin.auth_admin import admin_login, admin_logout, admin_register
from StudentManagementSystem.views.admin.dashboard_admin import  create_teacher, admin_dashboard

urlpatterns = [
    path('', admin_login, name='admin_login'),
    path('logout/', admin_logout, name='admin_logout'),
    path('register/', admin_register, name='admin_register'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('create-teacher/', create_teacher, name='create_teacher'),
]