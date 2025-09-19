import string

from django.db import transaction
from django.db.models import Prefetch
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.pre_post_test import TestDefinition, TestQuestion, TestChoice
from StudentManagementSystem.models.roles import Role


@session_login_required(role=Role.TEACHER)
def pre_post_test_view(request):
    teacher = request.user_obj

    if request.method == "POST":
        name = request.POST.get("name")
        test_type = request.POST.get("test_type")
        description = request.POST.get("description")
        shuffle_q = bool(request.POST.get("shuffle_questions"))
        shuffle_c = bool(request.POST.get("shuffle_choices"))

        if not name:
            messages.error(request, "❌ Test name is required!")
        else:
            test = TestDefinition.objects.create(
                name=name,
                test_type=test_type,
                description=description,
                shuffle_questions=shuffle_q,
                shuffle_choices=shuffle_c,
            )
            messages.success(request, f"✅ Test '{test.name}' created successfully!")
            return redirect("pre_post_test_view")

    tests = TestDefinition.objects.all().order_by("-created_at")

    return render(
        request,
        "teacher/main/pre_post_test.html",
        {
            "username": f"{teacher.first_name} {teacher.last_name}",
            "role": teacher.role,
            "tests": tests,
        },
    )


@session_login_required(role=Role.TEACHER)
def manage_test_view(request, test_id):
    teacher = request.user_obj
    test = get_object_or_404(TestDefinition, id=test_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_question":
            return _handle_add_question(request, test)

    # ✅ prefetch choices in stable order
    ordered_choices = TestChoice.objects.order_by("sort_order", "id")
    questions = (
        test.questions.prefetch_related(
            Prefetch("choices", queryset=ordered_choices)
        )
        .all()
    )

    # ✅ attach labels dynamically (A, B, C...)
    for q in questions:
        for i, c in enumerate(q.choices.all()):
            c.label = string.ascii_uppercase[i]

    return render(
        request,
        "teacher/main/manage_test.html",
        {
            "test": test,
            "questions": questions,
            "username": f"{teacher.first_name} {teacher.last_name}",
            "role": teacher.role,
        },
    )


def _handle_add_question(request, test):
    text = request.POST.get("question_text")
    points = float(request.POST.get("points") or 1)
    required = bool(request.POST.get("required"))

    q = TestQuestion.objects.create(
        test=test, text=text, points=points, required=required
    )

    choice_texts = request.POST.getlist("choice_text[]")
    correct_index = request.POST.get("is_correct")  # single radio button index

    for idx, ctext in enumerate(choice_texts):
        TestChoice.objects.create(
            question=q,
            text=ctext,
            is_correct=(str(idx) == str(correct_index)),
            sort_order=idx,
        )

    messages.success(request, f"✅ Question with choices added to {test.name}")
    return redirect("manage_test_view", test_id=test.id)


@session_login_required(role=Role.TEACHER)
@require_POST
def update_question_ajax(request, test_id, question_id):
    q = get_object_or_404(TestQuestion, id=question_id, test_id=test_id)
    q.text = request.POST.get("text", q.text)
    q.points = float(request.POST.get("points") or q.points)
    q.save(update_fields=["text", "points"])
    return JsonResponse({"status": "ok", "text": q.text, "points": q.points})


@session_login_required(role=Role.TEACHER)
@require_POST
@transaction.atomic
def update_choice_ajax(request, test_id, question_id, choice_id):
    c = get_object_or_404(
        TestChoice, id=choice_id, question_id=question_id, question__test_id=test_id
    )

    c.text = request.POST.get("text", c.text)
    val = str(request.POST.get("is_correct", "")).lower()
    is_correct = val in ["true", "1", "on", "yes"]

    if is_correct:
        # ensure only one correct per question
        TestChoice.objects.filter(question_id=question_id).update(is_correct=False)

    c.is_correct = is_correct
    c.save(update_fields=["text", "is_correct"])

    return JsonResponse({"status": "ok", "text": c.text, "is_correct": c.is_correct})


@session_login_required(role=Role.TEACHER)
@require_POST
def delete_question_ajax(request, test_id, question_id):
    q = get_object_or_404(TestQuestion, id=question_id, test_id=test_id)
    q.delete()
    return JsonResponse({"status": "ok", "deleted_id": question_id})


@session_login_required(role=Role.TEACHER)
@require_POST
def delete_choice_ajax(request, test_id, question_id, choice_id):
    c = get_object_or_404(
        TestChoice, id=choice_id, question_id=question_id, question__test_id=test_id
    )
    c.delete()
    return JsonResponse({"status": "ok", "deleted_id": choice_id})
