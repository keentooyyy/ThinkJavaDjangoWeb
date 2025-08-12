from django.urls import path

from StudentManagementSystem.views.students.auth_students import student_register, student_login, student_logout
from StudentManagementSystem.views.students.dashboard_students import student_dashboard

urlpatterns = [
    path('register/', student_register, name='student_register'),
    path('login/', student_login, name='student_login'),
    path('logout/', student_logout, name='student_logout'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
]
