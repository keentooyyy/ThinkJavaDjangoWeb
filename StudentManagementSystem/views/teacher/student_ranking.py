from django.shortcuts import render

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, Notification
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Department
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.views.ranking_view import (
    get_common_params,
    deduplicate_sections,
    paginate_queryset,
    build_ranking_context,
)


@session_login_required(role=Role.TEACHER)
def teacher_student_ranking(request):
    teacher = request.user_obj  # ✅ validated Teacher from decorator
    user_context = {"username": f"{teacher.first_name} {teacher.last_name}", "role": teacher.role}

    params = get_common_params(request)

    # handled sections for this teacher
    all_handled_sections = (
        HandledSection.objects.filter(teacher=teacher)
        .select_related("section__year_level", "department")
        .order_by("department__name", "section__year_level__year", "section__letter")
    )

    handled_sections = all_handled_sections
    if params["department_name"] and params["department_name"].lower() != "all":
        handled_sections = handled_sections.filter(department__name=params["department_name"])

    unique_sections = deduplicate_sections([hs.section for hs in handled_sections])

    student_ids = Student.objects.filter(
        section__in=handled_sections.values_list("section_id", flat=True)
    ).values_list("id", flat=True)

    # get base rankings
    rankings = get_all_student_rankings(
        sort_by=params["sort_by"],
        sort_order=params["sort_order"],
        filter_by=params["section_filter"],
        department_filter=None if params["department_name"] and params["department_name"].lower() == "all"
        else params["department_name"],
        limit_to_students=student_ids,
    )

    # ✅ Apply search filter if provided
    search_query = request.GET.get("search", "").strip().lower()
    if search_query:
        rankings = [
            r for r in rankings
            if search_query in str(r.get("student_id", "")).lower()
               or search_query in str(r.get("first_name", "")).lower()
               or search_query in str(r.get("last_name", "")).lower()
               or search_query in f"{r.get('first_name', '')} {r.get('last_name', '')}".lower()
               or search_query in str(r.get("section", "")).lower()
               or search_query in str(r.get("score", "")).lower()
        ]

    # paginate results
    page_obj = paginate_queryset(rankings, params["per_page"], params["page_number"])
    notifications = Notification.objects.filter(
        recipient_role=Role.TEACHER,
        teacher_recipient=teacher
    ).order_by("-created_at")  # last 10

    unread_count = notifications.filter(is_read=False).count()

    context = build_ranking_context(rankings, page_obj, params, user_context, {
        "departments": Department.objects.filter(
            id__in=all_handled_sections.values_list("department_id", flat=True).distinct()
        ).order_by("name"),
        "sections": unique_sections,
        "selected_department": params["department_name"],
        "selected_section": params["section_filter"],
        "notifications": notifications,
        "unread_count": unread_count,
    })

    return render(request, "student_ranking.html", context)
