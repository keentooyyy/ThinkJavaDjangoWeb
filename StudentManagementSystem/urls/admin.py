from django.urls import path

from StudentManagementSystem.views.admin.auth_admin import admin_register
from StudentManagementSystem.views.admin.dashboard_admin import dashboard_ranking, admin_dashboard
from StudentManagementSystem.views.admin.manage_teachers import create_teacher, get_teacher_details, \
    edit_teacher, remove_section, delete_teacher
from StudentManagementSystem.views.admin.proggress_addition_admin import add_achievement, add_level, delete_achievement, \
    delete_level, force_sync_everyone
from StudentManagementSystem.views.admin.student_ranking import admin_student_ranking
from StudentManagementSystem.views.auth_unified import unified_login, unified_logout, register_student
from StudentManagementSystem.views.edit_profile import edit_profile
from StudentManagementSystem.views.logger import view_log

urlpatterns = [
    # Login and Logout Routes
    path('', unified_login, name='unified_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('admin-register/', admin_register, name='admin_register'),
    path('register/', register_student, name='register'),

    # Dashboard
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    # Edit Profile
    path("profile/", edit_profile, name="edit_profile"),

    # JSON Endpoints
    path("ranking/", dashboard_ranking, name="dashboard_ranking"),

    # Teacher Management Routes
    path('create-teacher/', create_teacher, name='create_teacher'),
    path('admin_teacher/<int:teacher_id>/get_details/', get_teacher_details, name='get_teacher_details'),
    # Fetch details for the modal
    path('admin_teacher/<int:teacher_id>/edit/', edit_teacher, name='edit_teacher'),  # Edit teacher
    path('admin_teacher/remove_section/<int:section_id>/', remove_section, name='remove_section'),
    path('admin_teacher/delete/<int:teacher_id>/', delete_teacher, name='delete_teacher'),

    # Student Ranking
    path('student_rankings/', admin_student_ranking, name='admin_student_ranking'),

    # Game Progression Routes,
    path('add-level/', add_level, name='add_level'),
    path('add-achievement/', add_achievement, name='add_achievement'),
    path('delete_level/<int:level_id>/', delete_level, name='delete_level'),
    path('delete_achievement/<int:achievement_id>/', delete_achievement, name='delete_achievement'),
    path('force_sync/', force_sync_everyone, name='force_sync'),

    path('logs/', view_log, name='admin_view_logs')
]
