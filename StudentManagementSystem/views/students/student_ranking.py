from django.core.paginator import Paginator
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect, render

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role


def student_ranking(request):
    # Get logged-in student
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or role != Role.STUDENT:
        return HttpResponseForbidden("You do not have permission to access this page.")

    try:
        student = Student.objects.select_related(
            "section", "year_level", "section__department"
        ).get(id=user_id)
    except Student.DoesNotExist:
        return redirect("unified_logout")

    if not student.section:
        return HttpResponseForbidden("You are not assigned to any section.")

    # Sorting + pagination params
    sort_by = request.GET.get("sort_by", "")
    sort_order = request.GET.get("sort_order", "desc")
    page_number = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 25))

    # 🔹 ensure we only fetch rankings for students in this section
    student_ids = Student.objects.filter(section=student.section).values_list("id", flat=True)


    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=f"{student.section.year_level.year}{student.section.letter}",
        department_filter=student.section.department.name,
        limit_to_students=student_ids,
    )
    print(f"Ranking Student View:{rankings}")

    # Pagination
    paginator = Paginator(rankings, per_page)
    page_obj = paginator.get_page(page_number)

    full_name = f"{student.first_name} {student.last_name}"

    context = {
        "section": student.section,
        "rankings": page_obj.object_list,
        "page_obj": page_obj,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "per_page": per_page,
        "username": full_name,
        "role": role,
    }

    return render(request, "admin/student_ranking.html", context)
