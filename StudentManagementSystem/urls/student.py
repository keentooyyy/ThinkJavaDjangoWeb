from django.urls import path

from StudentManagementSystem.views.auth_unified import unified_logout
from StudentManagementSystem.views.students.auth_students import student_register
# from StudentManagementSystem.views.students.auth_students import student_register, student_login, student_logout
from StudentManagementSystem.views.students.dashboard_students import student_dashboard

urlpatterns = [
    path('register/', student_register, name='student_register'),
    # path('login/', student_login, name='student_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
]
