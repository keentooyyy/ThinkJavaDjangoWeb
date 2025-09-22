from django.db.models.aggregates import Sum
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student
from StudentManagementSystem.models.pre_post_test import TestDefinition, StudentTest, TestQuestion, TestChoice
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.views.teacher.manage_test import _parse_checkbox


@session_login_required(role=Role.TEACHER)
def pre_post_test_view(request):
    teacher = request.user_obj

    if request.method == "POST":
        name = request.POST.get("name")
        test_type = request.POST.get("test_type")
        shuffle_q = _parse_checkbox(request.POST.get("shuffle_questions"))
        shuffle_c = _parse_checkbox(request.POST.get("shuffle_choices"))

        if not name:
            messages.error(request, "❌ Test name is required!")
        else:
            test = TestDefinition.objects.create(
                name=name,
                test_type=test_type,
                shuffle_questions=shuffle_q,
                shuffle_choices=shuffle_c,
            )
            messages.success(request, f"✅ Test '{test.name}' created successfully!")
            return redirect("pre_post_test_view")

    tests = TestDefinition.objects.all().order_by("-created_at")

    # ✅ Build map of test_id → [section_ids]
    assigned_map = {
        t.id: list(t.assignments.values_list("section_id", flat=True))
        for t in tests
    }

    return render(
        request,
        "teacher/main/pre_post_test.html",
        {
            "username": f"{teacher.first_name} {teacher.last_name}",
            "role": teacher.role,
            "tests": tests,
            "test_types": TestDefinition.TEST_TYPE_CHOICES,
            "assigned_map": assigned_map,   # 🔹 new context
        },
    )


@session_login_required(role=Role.TEACHER)
def all_test_results_view(request):
    teacher = request.user_obj

    # ✅ Get sections this teacher handles
    handled_sections = Section.objects.filter(
        id__in=HandledSection.objects.filter(teacher=teacher).values("section_id")
    )

    # ✅ Students in those sections
    students = Student.objects.filter(section__in=handled_sections)

    # ✅ Results for those students
    results = (
        StudentTest.objects.filter(student__in=students)
        .select_related("student", "test")
        .order_by("test__created_at", "student__last_name", "student__first_name")
    )

    # ✅ Pre-calc max points per test
    max_points_map = {
        t["test"]: t["total_points"]
        for t in TestQuestion.objects.values("test").annotate(total_points=Sum("points"))
    }

    # ✅ Group results by test
    grouped = {}
    for r in results:
        if r.test_id not in grouped:
            grouped[r.test_id] = {
                "test": r.test,
                "max_points": max_points_map.get(r.test_id, 0),
                "rows": []
            }
        grouped[r.test_id]["rows"].append(r)

    return render(
        request,
        "teacher/main/pre_post_test.html",
        {
            "grouped_results": grouped,
            "handled_sections": handled_sections,
        },
    )

@session_login_required(role=Role.TEACHER)
@transaction.atomic
def duplicate_test(request, test_id):
    orig = TestDefinition.objects.get(id=test_id)

    # Clone test definition
    new_test = TestDefinition.objects.create(
        name=f"{orig.name} (Copy)",
        test_type=orig.test_type,
        shuffle_questions=orig.shuffle_questions,
        shuffle_choices=orig.shuffle_choices,
    )

    # Clone questions + choices
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

    messages.success(request, f"✅ Test '{orig.name}' duplicated successfully!")
    return redirect("pre_post_test_view")