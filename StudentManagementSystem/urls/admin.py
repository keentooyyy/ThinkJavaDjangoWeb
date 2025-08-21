from django.urls import path

from StudentManagementSystem.views.admin.apis.helper_functions_admin import get_sections_by_department
from StudentManagementSystem.views.admin.auth_admin import admin_register
from StudentManagementSystem.views.admin.dashboard_admin import admin_dashboard
from StudentManagementSystem.views.admin.manage_teachers import create_teacher, get_teacher_details, \
    edit_teacher, remove_section, delete_teacher
from StudentManagementSystem.views.admin.proggress_addition_admin import add_achievement, add_level
from StudentManagementSystem.views.admin.ranking_students import student_ranking
from StudentManagementSystem.views.auth_unified import unified_login, unified_logout

urlpatterns = [
    # Login and Logout Routes
    path('', unified_login, name='unified_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('register/', admin_register, name='admin_register'),

    # Dashboard
    path('dashboard/', admin_dashboard, name='admin_dashboard'),

    # Teacher Management Routes
    path('create-teacher/', create_teacher, name='create_teacher'),
    path('admin_teacher/<int:teacher_id>/get_details/', get_teacher_details, name='get_teacher_details'),
    # Fetch details for the modal
    path('admin_teacher/<int:teacher_id>/edit/', edit_teacher, name='edit_teacher'),  # Edit teacher
    path('admin_teacher/remove_section/<int:section_id>/', remove_section, name='remove_section'),
    path('admin_teacher/delete/<int:teacher_id>/', delete_teacher, name='delete_teacher'),

    # Student Ranking
    path('student_rankings/', student_ranking, name='student_ranking'),

    # Other Routes
    path('get-sections-by-department/', get_sections_by_department, name='get_sections_by_department'),
    path('add-level/', add_level, name='add_level'),
    path('add-achievement/', add_achievement, name='add_achievement'),
]
