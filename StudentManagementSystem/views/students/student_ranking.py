from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role
from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.views.ranking_view import (
    get_common_params,
    paginate_queryset,
    build_ranking_context,
)


def student_student_ranking(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or role != Role.STUDENT:
        return HttpResponseForbidden("Forbidden")

    try:
        student = Student.objects.select_related(
            "section", "year_level", "section__department"
        ).get(id=user_id)
    except Student.DoesNotExist:
        return redirect("unified_logout")

    if not student.section:
        return HttpResponseForbidden("You are not assigned to any section.")

    params = get_common_params(request)

    student_ids = Student.objects.filter(
        section=student.section
    ).values_list("id", flat=True)

    rankings = get_all_student_rankings(
        sort_by=params["sort_by"],
        sort_order=params["sort_order"],
        filter_by=f"{student.section.year_level.year}{student.section.letter}",
        department_filter=student.section.department.name,
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
            or search_query in f"{r.get('first_name', '')} {r.get('last_name', '')}".lower()  # full name
            or search_query in str(r.get("section", "")).lower()
            or search_query in str(r.get("score", "")).lower()
        ]

    # ✅ Paginate after filtering
    page_obj = paginate_queryset(rankings, params["per_page"], params["page_number"])

    user_context = {"username": f"{student.first_name} {student.last_name}", "role": role}

    context = build_ranking_context(
        rankings, page_obj, params, user_context, {
            "section": student.section,
        }
    )

    return render(request, "admin/../../templates/student_ranking.html", context)
