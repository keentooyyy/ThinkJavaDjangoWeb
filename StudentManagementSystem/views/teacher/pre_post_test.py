import string
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.pre_post_test import TestDefinition, TestQuestion, TestChoice
from StudentManagementSystem.models.roles import Role


# -----------------------------
# 🔹 Helpers
# -----------------------------
def _get_test(test_id):
    return get_object_or_404(TestDefinition, id=test_id)

def _get_question(test_id, question_id):
    return get_object_or_404(TestQuestion, id=question_id, test_id=test_id)

def _get_choice(test_id, question_id, choice_id):
    return get_object_or_404(TestChoice, id=choice_id, question_id=question_id, question__test_id=test_id)

def _parse_checkbox(value):
    if value is None:
        return False
    return str(value).lower() in ("1", "true", "on", "yes")

def _update_test_fields(test, data, only_settings=False):
    """Update TestDefinition from POST/Dict"""
    if not only_settings:
        test.name = data.get("name", test.name)
        test.test_type = data.get("test_type", test.test_type)
    test.shuffle_questions = _parse_checkbox(data.get("shuffle_questions"))
    test.shuffle_choices = _parse_checkbox(data.get("shuffle_choices"))
    # print("Parsed shuffle_choices:", test.shuffle_choices)
    # print("Parsed shuffle_questions:", test.shuffle_questions)
    return test

def _json_ok(extra=None):
    res = {"status": "ok"}
    if extra:
        res.update(extra)
    return JsonResponse(res)


# -----------------------------
# 🔹 Views (unchanged as requested)
# -----------------------------
@session_login_required(role=Role.TEACHER)
def pre_post_test_view(request):
    teacher = request.user_obj

    if request.method == "POST":
        name = request.POST.get("name")
        test_type = request.POST.get("test_type")
        shuffle_q = bool(request.POST.get("shuffle_questions"))
        shuffle_c = bool(request.POST.get("shuffle_choices"))

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

    return render(
        request,
        "teacher/main/pre_post_test.html",
        {
            "username": f"{teacher.first_name} {teacher.last_name}",
            "role": teacher.role,
            "tests": tests,
            "test_types": TestDefinition.TEST_TYPE_CHOICES,
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

    ordered_choices = TestChoice.objects.order_by("sort_order", "id")
    questions = (
        test.questions.prefetch_related(
            Prefetch("choices", queryset=ordered_choices)
        ).all()
    )
    total_points = (
        TestQuestion.objects.filter(test=test)
        .aggregate(total=Sum("points"))["total"] or 0
    )
    return render(
        request,
        "teacher/main/manage_test.html",
        {
            "test": test,
            "total_points": total_points,
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
    correct_index = request.POST.get("is_correct")

    for idx, ctext in enumerate(choice_texts):
        TestChoice.objects.create(
            question=q,
            text=ctext,
            is_correct=(str(idx) == str(correct_index)),
            sort_order=idx,
        )

    messages.success(request, f"✅ Question with choices added to {test.name}")
    return redirect("manage_test_view", test_id=test.id)


# -----------------------------
# 🔹 Test CRUD
# -----------------------------
@session_login_required(role=Role.TEACHER)
@require_POST
def update_test(request, test_id):
    test = _update_test_fields(_get_test(test_id), request.POST)
    test.save(update_fields=["name", "test_type", "shuffle_questions", "shuffle_choices"])
    messages.success(request, f"✅ Test '{test.name}' updated successfully.")
    return redirect("manage_test_view", test_id=test.id)


@session_login_required(role=Role.TEACHER)
@require_POST
def update_test_settings(request, test_id):
    test = _update_test_fields(_get_test(test_id), request.POST, only_settings=True)
    test.save(update_fields=["shuffle_questions", "shuffle_choices"])
    messages.success(request, f"Settings updated for {test.name}")
    return redirect("manage_test_view", test_id=test.id)


@session_login_required(role=Role.TEACHER)
@require_POST
def delete_test(request, test_id):
    test = _get_test(test_id)
    name = test.name
    test.delete()
    messages.success(request, f"Test '{name}' deleted successfully.")
    return redirect("pre_post_test_view")


# -----------------------------
# 🔹 Question / Choice AJAX
# -----------------------------
@session_login_required(role=Role.TEACHER)
@require_POST
def delete_choice_ajax(request, test_id, question_id, choice_id):
    _get_choice(test_id, question_id, choice_id).delete()
    return _json_ok({"deleted_id": choice_id})


@session_login_required(role=Role.TEACHER)
@require_POST
@transaction.atomic
def save_question_ajax(request, test_id, question_id):
    q = _get_question(test_id, question_id)
    q.text = request.POST.get("text", q.text)
    q.points = float(request.POST.get("points") or q.points)
    q.save(update_fields=["text", "points"])

    # update/add choices
    choices = request.POST.getlist("choices[]")
    correct_id = request.POST.get("correct_id")

    for idx, raw in enumerate(choices):
        cid, ctext = raw.split("::", 1) if "::" in raw else (None, raw)

        if cid and cid.isdigit():
            c = TestChoice.objects.get(id=int(cid), question=q)
            c.text, c.sort_order = ctext, idx
            c.is_correct = str(cid) == str(correct_id)
            c.save(update_fields=["text", "is_correct", "sort_order"])
        else:
            TestChoice.objects.create(
                question=q, text=ctext, is_correct=False, sort_order=idx
            )

    if correct_id and correct_id.isdigit():
        TestChoice.objects.filter(question=q).update(is_correct=False)
        TestChoice.objects.filter(id=int(correct_id), question=q).update(is_correct=True)

    return _json_ok()


@session_login_required(role=Role.TEACHER)
@require_POST
def reorder_choices_ajax(request, test_id, question_id):
    q = _get_question(test_id, question_id)
    ids = request.POST.getlist("order[]")
    for idx, cid in enumerate(ids):
        TestChoice.objects.filter(id=cid, question=q).update(sort_order=idx)
    return _json_ok({"new_order": ids})


@session_login_required(role=Role.TEACHER)
@require_POST
def delete_question_ajax(request, test_id, question_id):
    _get_question(test_id, question_id).delete()
    return _json_ok({"deleted_id": question_id})
