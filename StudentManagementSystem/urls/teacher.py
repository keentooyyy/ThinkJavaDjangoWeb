from django.urls import path

from StudentManagementSystem.views.teacher import register_student_teacher
from StudentManagementSystem.views.teacher.auth_teacher import teacher_login, teacher_logout
from StudentManagementSystem.views.teacher.dashboard_teacher import teacher_dashboard

urlpatterns = [
    path('login/', teacher_login, name='teacher_login'),
    path('logout/', teacher_logout, name='teacher_logout'),
    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/register-student/', register_student_teacher.register_student_teacher,
         name='register_student_teacher'),
]
