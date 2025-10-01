from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, Notification
from StudentManagementSystem.models.pre_post_test import (
    TestDefinition, StudentTest, TestQuestion, TestChoice
)
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.views.logger import create_log
from StudentManagementSystem.views.teacher.manage_test import _parse_checkbox


# ------------------------------
# Context Builders
# ------------------------------

def _get_base_context(teacher):
    notifications = Notification.objects.filter(
        recipient_role=Role.TEACHER,
        teacher_recipient=teacher
    ).order_by("-created_at")  # last 10

    unread_count = notifications.filter(is_read=False).count()
    return {
        "username": f"{teacher.first_name} {teacher.last_name}",
        "role": teacher.role,
        'notifications': notifications,
        'unread_count': unread_count,
    }


def _get_teacher_test_context(teacher):
    context = _get_base_context(teacher)

    tests = TestDefinition.objects.all().order_by("-created_at")
    assigned_map = {
        t.id: list(t.assignments.values_list("section_id", flat=True))
        for t in tests
    }
    handled_sections = Section.objects.filter(
        id__in=HandledSection.objects.filter(teacher=teacher).values("section_id")
    )

    context.update({
        "tests": tests,
        "test_types": TestDefinition.TEST_TYPE_CHOICES,
        "assigned_map": assigned_map,
        "handled_sections": handled_sections,
    })
    return context


def _get_teacher_results_context(request, teacher):
    context = _get_base_context(teacher)

    handled_sections = HandledSection.objects.filter(teacher=teacher).values_list("section_id", flat=True)
    students = Student.objects.filter(section_id__in=handled_sections)

    selected_type = request.GET.get("test_type")
    selected_test_id = request.GET.get("test_id")

    query = StudentTest.objects.filter(student__in=students, completed=True)

    if selected_type in [TestDefinition.PRE, TestDefinition.POST]:
        query = query.filter(test__test_type=selected_type)

    if selected_test_id:
        query = query.filter(test_id=selected_test_id)

    results = query.select_related(
        "student__section__department", "student__section__year_level", "test"
    ).order_by("test__created_at", "student__last_name", "student__first_name")

    max_points_map = {
        t["test"]: t["total_points"]
        for t in TestQuestion.objects.values("test").annotate(total_points=Sum("points"))
    }

    grouped_results = {}
    for r in results:
        if r.test_id not in grouped_results:
            grouped_results[r.test_id] = {
                "test": r.test,
                "max_points": max_points_map.get(r.test_id, 0),
                "rows": []
            }
        grouped_results[r.test_id]["rows"].append(r)

    context.update({
        "grouped_results": grouped_results,
        "handled_sections": Section.objects.filter(id__in=handled_sections),
        "selected_test_type": selected_type,
        "selected_test_id": selected_test_id,
        "available_tests": TestDefinition.objects.filter(
            test_type=selected_type
        ) if selected_type else TestDefinition.objects.all(),
    })
    return context


# ------------------------------
# Views
# ------------------------------

@session_login_required(role=Role.TEACHER)
def pre_post_test_view(request):
    teacher = request.user_obj

    if request.method == "POST":
        name = request.POST.get("name")
        test_type = request.POST.get("test_type")
        shuffle_q = _parse_checkbox(request.POST.get("shuffle_questions"))
        shuffle_c = _parse_checkbox(request.POST.get("shuffle_choices"))

        if not name:
            messages.error(request, "Test name is required.")
        else:
            test = TestDefinition.objects.create(
                name=name,
                test_type=test_type,
                shuffle_questions=shuffle_q,
                shuffle_choices=shuffle_c,
            )
            create_log(request, "CREATE", f"Created test '{test.name}' ({test.test_type})")
            messages.success(request, f"Test '{name}' created successfully.")
            return redirect("pre_post_test_view")

    context = _get_teacher_test_context(teacher)
    context.update(_get_teacher_results_context(request, teacher))
    return render(request, "teacher/main/pre_post_test.html", context)


@session_login_required(role=Role.TEACHER)
@transaction.atomic
def duplicate_test(request, test_id):
    orig = get_object_or_404(TestDefinition, id=test_id)

    new_test = TestDefinition.objects.create(
        name=f"{orig.name} (Copy)",
        test_type=orig.test_type,
        shuffle_questions=orig.shuffle_questions,
        shuffle_choices=orig.shuffle_choices,
    )

    for q in orig.questions.all():
        new_q = TestQuestion.objects.create(
            test=new_test,
            text=q.text,
            points=q.points,
            required=q.required,
            sort_order=q.sort_order,
        )
        for c in q.choices.all():
            TestChoice.objects.create(
                question=new_q,
                text=c.text,
                is_correct=c.is_correct,
                sort_order=c.sort_order,
            )

    create_log(request, "CREATE", f"Duplicated test '{orig.name}' to '{new_test.name}'")
    messages.success(request, f"Test '{orig.name}' duplicated successfully.")
    return redirect("pre_post_test_view")
