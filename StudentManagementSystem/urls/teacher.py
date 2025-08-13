from django.urls import path

from StudentManagementSystem.views.auth_unified import unified_logout
# from StudentManagementSystem.views.teacher.auth_teacher import teacher_login, teacher_logout
from StudentManagementSystem.views.teacher.dashboard_teacher import teacher_dashboard
from StudentManagementSystem.views.teacher.edit_profile import edit_profile
from StudentManagementSystem.views.teacher.generate_section_code_teacher import generate_section_code_view
from StudentManagementSystem.views.teacher.progress_control_teacher import progress_control_teacher
from StudentManagementSystem.views.teacher.register_student_teacher import register_student_teacher

urlpatterns = [
    # path('login/', teacher_login, name='teacher_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('register-student/', register_student_teacher,
         name='register_student_teacher'),
    path('generate-section-code/', generate_section_code_view, name='generate_section_code'),
    path('edit/profile/<int:teacher_id>/', edit_profile, name='edit_profile'),
    path('progress-control/', progress_control_teacher, name='progress_control_teacher'),

]
