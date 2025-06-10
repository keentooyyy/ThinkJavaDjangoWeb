# StudentManagementSystem/views/rankings.py

from django.shortcuts import render
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from GameProgress.services.ranking import get_all_student_rankings


def student_rankings_view(request):
    # Extract filters from GET params
    department_name = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by", "score")
    sort_order = request.GET.get("sort_order", "desc")

    # Load available departments and sections
    departments = Department.objects.all().order_by("name")
    sections = Section.objects.filter(department__name=department_name).order_by("year_level__year", "letter") if department_name else []

    # Get rankings from core function
    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=section_filter,
        department_filter=department_name,
    )

    context = {
        "rankings": rankings,
        "departments": departments,
        "sections": sections,
        "selected_department": department_name,
        "selected_section": section_filter,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    return render(request, "admin/dashboard.html", context)
