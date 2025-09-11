from django.http import HttpResponseForbidden
from django.shortcuts import render

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.views.ranking_view import (
    get_common_params,
    deduplicate_sections,
    paginate_queryset,
    build_ranking_context,
)


@session_login_required(role=Role.ADMIN)
def admin_student_ranking(request):
    try:
        admin = SimpleAdmin.objects.get(id=request.session.get("user_id"))
        user_context = {"username": admin.username, "role": admin.role}
    except SimpleAdmin.DoesNotExist:
        return HttpResponseForbidden("Forbidden")

    if user_context["role"] != Role.ADMIN:
        return HttpResponseForbidden("Forbidden")

    params = get_common_params(request)

    # Admin sees all departments + all sections
    departments = Department.objects.all().order_by("name")
    sections = Section.objects.select_related("year_level").order_by("year_level__year", "letter")
    unique_sections = deduplicate_sections(sections)

    rankings = get_all_student_rankings(
        sort_by=params["sort_by"],
        sort_order=params["sort_order"],
        filter_by=params["section_filter"],
        department_filter=None if not params["department_name"] or params["department_name"].lower() == "all"
                                else params["department_name"],
    )

    # ✅ Apply search filter if provided
    search_query = request.GET.get("search", "").strip().lower()
    if search_query:
        rankings = [
            r for r in rankings
            if search_query in str(r.get("student_id", "")).lower()
               or search_query in str(r.get("first_name", "")).lower()
               or search_query in str(r.get("last_name", "")).lower()
               or search_query in f"{r.get('first_name', '')} {r.get('last_name', '')}".lower()  # ✅ full name
               or search_query in str(r.get("section", "")).lower()
               or search_query in str(r.get("score", "")).lower()
        ]

    # ✅ Paginate AFTER filtering
    page_obj = paginate_queryset(rankings, params["per_page"], params["page_number"])

    context = build_ranking_context(rankings, page_obj, params, user_context, {
        "departments": departments,
        "sections": unique_sections,
        "selected_department": params["department_name"],
        "selected_section": params["section_filter"],
    })

    return render(request, "admin/../../templates/student_ranking.html", context)
