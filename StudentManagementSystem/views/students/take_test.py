from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Notification
from StudentManagementSystem.models.pre_post_test import (
    TestDefinition, StudentTest, TestChoice,
    StudentAnswer, StudentProgress
)
from StudentManagementSystem.models.roles import Role


@session_login_required(role=Role.STUDENT)
def take_test_view(request):
    student = request.user_obj
    username = f"{student.first_name} {student.last_name}"
    role = student.role

    def get_progress(test):
        if not test:
            return None
        progress, _ = StudentProgress.objects.get_or_create(student=student, test=test)
        progress.init_order()  # ensures shuffle is applied once
        return progress

    # ----- Pre-Test -----
    pre_test = (
        TestDefinition.objects.filter(
            test_type=TestDefinition.PRE,
            assignments__section=student.section
        )
        .order_by("created_at")
        .first()
    )
    pre_progress = get_progress(pre_test)
    pre_taken = StudentTest.objects.filter(
        student=student, test=pre_test, completed=True
    ).first() if pre_test else None

    # Always compute max if test exists
    pre_max = sum(q.points for q in pre_test.questions.all()) if pre_test else None
    pre_score = pre_taken.score if pre_taken else None

    # Build choices map for pre-test
    pre_choices_map = {}
    if pre_progress:
        for q in pre_progress.get_page_questions():
            pre_choices_map[q.id] = pre_progress.get_choices_for_question(q)

    # ----- Post-Test -----
    post_test = (
        TestDefinition.objects.filter(
            test_type=TestDefinition.POST,
            assignments__section=student.section
        )
        .order_by("created_at")
        .first()
    )
    post_progress = get_progress(post_test)
    post_taken = StudentTest.objects.filter(
        student=student, test=post_test, completed=True
    ).first() if post_test else None

    # Always compute max if test exists
    post_max = sum(q.points for q in post_test.questions.all()) if post_test else None
    post_score = post_taken.score if post_taken else None

    # Build choices map for post-test
    post_choices_map = {}
    if post_progress:
        for q in post_progress.get_page_questions():
            post_choices_map[q.id] = post_progress.get_choices_for_question(q)

    notifications = Notification.objects.filter(
        recipient_role=Role.STUDENT,
        student_recipient=student
    ).order_by("-created_at")  # last 10

    unread_count = notifications.filter(is_read=False).count()

    context = {
        "username": username,
        "role": role,

        "pre_test": pre_test,
        "pre_taken": pre_taken,
        "pre_score": pre_score,
        "pre_max": pre_max,
        "pre_progress": pre_progress,
        "pre_choices_map": pre_choices_map,

        "post_test": post_test,
        "post_taken": post_taken,
        "post_score": post_score,
        "post_max": post_max,
        "post_progress": post_progress,
        "post_choices_map": post_choices_map,

        "can_take_posttest": student.can_take_posttest,

        "notifications": notifications,
        "unread_count": unread_count,
    }
    return render(request, "students/main/take_test.html", context)


@session_login_required(role=Role.STUDENT)
@require_POST
def submit_test(request, test_id):
    student = request.user_obj
    test = get_object_or_404(TestDefinition, id=test_id)

    # Get or create student test
    stest, _ = StudentTest.objects.get_or_create(student=student, test=test)

    # Collect unanswered required questions
    missing_required = []
    for q in test.questions.all():
        choice_id = request.POST.get(f"q{q.id}")
        if choice_id:
            choice = TestChoice.objects.get(id=choice_id, question=q)
            StudentAnswer.objects.update_or_create(
                student=student,
                question=q,
                defaults={"choice": choice, "is_correct": choice.is_correct},
            )
        elif q.required:
            missing_required.append(q)

    # If required questions are missing → block submission
    if missing_required:
        messages.error(
            request,
            f"❌ You must answer all required questions before submitting. "
            f"Missing: {len(missing_required)} question(s)."
        )
        return redirect("take_test_view")

    # Grade it
    result = stest.grade_test()

    # Feedback
    messages.success(
        request,
        f"✅ You scored {result['score']} out of {result['max_score']} on {test.name}."
    )
    return redirect("take_test_view")
