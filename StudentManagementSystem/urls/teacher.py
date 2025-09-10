from django.urls import path

from StudentManagementSystem.views.auth_unified import unified_logout
from StudentManagementSystem.views.teacher.dashboard_teacher import teacher_dashboard
from StudentManagementSystem.views.teacher.edit_profile import edit_profile
from StudentManagementSystem.views.teacher.generate_section_code import generate_section_code_view, delete_section_code
from StudentManagementSystem.views.teacher.progress_control import progress_control_teacher
from StudentManagementSystem.views.teacher.student_ranking import teacher_student_ranking
from StudentManagementSystem.views.teacher.register_student import register_student, edit_student, delete_student

urlpatterns = [  # path('login/', teacher_login, name='teacher_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),

    # Student Management Routes
    path('register-student/', register_student, name='register_student'),
    path("students/<int:student_id>/edit/", edit_student, name="edit_student"),
    path("students/<int:student_id>/delete/", delete_student, name="delete_student"),
    path("teacher/student-ranking/", teacher_student_ranking, name="teacher_student_ranking"),

    path('generate-section-code/', generate_section_code_view, name='generate_section_code'),
    path("section-codes/delete/", delete_section_code, name="delete_section_code", ),

    path('edit/profile/<int:teacher_id>/', edit_profile, name='edit_profile'),

    # Game Progress Control Routes
    path('progress-control/', progress_control_teacher, name='progress_control_teacher'),

]
