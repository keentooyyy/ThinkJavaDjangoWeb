from django.urls import path

from StudentManagementSystem.views.auth_unified import unified_logout
# from StudentManagementSystem.views.students.auth_students import student_register, student_login, student_logout
from StudentManagementSystem.views.students.dashboard_students import student_dashboard
from StudentManagementSystem.views.students.student_ranking import student_student_ranking
from StudentManagementSystem.views.students.take_test import take_test_view, submit_test

urlpatterns = [
    # path('login/', student_login, name='student_login'),
    path('logout/', unified_logout, name='unified_logout'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('ranking/', student_student_ranking, name='student_ranking'),

    path("student/take-test/", take_test_view, name="take_test_view"),
    path("student/take-test/<int:test_id>/submit/", submit_test, name="submit_test"),

]
