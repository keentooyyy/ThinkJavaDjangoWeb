from django.urls import path

from StudentManagementSystem.views.auth_unified import unified_logout
from StudentManagementSystem.views.teacher.dashboard_teacher import teacher_dashboard
# from StudentManagementSystem.views.teacher.edit_profile import edit_profile
from StudentManagementSystem.views.teacher.generate_section_code import (
    generate_section_code_view,
    delete_section_code,
    check_section_code_exists,
)
from StudentManagementSystem.views.teacher.manage_test import (
    manage_test_view,
    delete_test,
    save_question_ajax,
    delete_question_ajax,
    delete_choice_ajax,
    reorder_choices_ajax,
    update_test,
)
from StudentManagementSystem.views.teacher.pre_post_test import pre_post_test_view
from StudentManagementSystem.views.teacher.progress_control import progress_control_teacher
from StudentManagementSystem.views.teacher.register_student import (
    register_student,
    edit_student,
    delete_student,
)
from StudentManagementSystem.views.teacher.student_ranking import teacher_student_ranking

# import the new view
from StudentManagementSystem.views.teacher.manage_test import assign_test

urlpatterns = [
    # Authentication
    path("logout/", unified_logout, name="unified_logout"),
    path("dashboard/", teacher_dashboard, name="teacher_dashboard"),

    # Student Management Routes
    path("register-student/", register_student, name="register_student"),
    path("students/<int:student_id>/edit/", edit_student, name="edit_student"),
    path("students/<int:student_id>/delete/", delete_student, name="delete_student"),
    path("teacher/student-ranking/", teacher_student_ranking, name="teacher_student_ranking"),

    # Section Code Routes
    path("generate-section-code/", generate_section_code_view, name="generate_section_code"),
    path("check-section-code/", check_section_code_exists, name="check_section_code_exists"),
    path("section-codes/delete/", delete_section_code, name="delete_section_code"),

    # Game Progress Control Routes
    path("progress-control/", progress_control_teacher, name="progress_control_teacher"),

    # Pre Post Test Routes
    path("pre-post-test/", pre_post_test_view, name="pre_post_test_view"),
    path("pre-post-test/<int:test_id>/", manage_test_view, name="manage_test_view"),

    # Test update + delete
    path("tests/<int:test_id>/update-meta/", update_test, name="update_test"),
    path("pre-post-test/<int:test_id>/delete/", delete_test, name="delete_test"),

    # Unified Question & Choice save
    path("pre-post-test/<int:test_id>/<int:question_id>/save/", save_question_ajax, name="save_question_ajax"),

    # Reorder + Delete
    path("pre-post-test/<int:test_id>/<int:question_id>/choices/reorder/", reorder_choices_ajax,
         name="reorder_choices_ajax"),
    path("pre-post-test/<int:test_id>/<int:question_id>/delete/", delete_question_ajax, name="delete_question_ajax"),
    path("pre-post-test/<int:test_id>/<int:question_id>/<int:choice_id>/delete/", delete_choice_ajax,
         name="delete_choice_ajax"),

    # New Assign Test route
    path("pre-post-test/<int:test_id>/assign/", assign_test, name="assign_test"),
]
