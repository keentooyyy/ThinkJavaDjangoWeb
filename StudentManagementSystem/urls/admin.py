from django.urls import path


from StudentManagementSystem.views.admin.apis.helper_functions_admin import get_sections_by_department
from StudentManagementSystem.views.admin.auth_admin import admin_login, admin_logout, admin_register
from StudentManagementSystem.views.admin.dashboard_admin import create_teacher, admin_dashboard
from StudentManagementSystem.views.admin.proggress_addition_admin import add_achievement, add_level

urlpatterns = [
    path('', admin_login, name='admin_login'),
    path('logout/', admin_logout, name='admin_logout'),
    path('register/', admin_register, name='admin_register'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('create-teacher/', create_teacher, name='create_teacher'),
    path('get-sections-by-department/', get_sections_by_department, name='get_sections_by_department'),
    path('add-level/', add_level, name='add_level'),
    path('add-achievement/', add_achievement, name='add_achievement'),

]
