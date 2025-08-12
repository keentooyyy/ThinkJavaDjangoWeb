from django.core.paginator import Paginator

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.student import Student


def get_rankings_context(request, teacher=None):
    department_name = request.GET.get("department")
    section_filter = request.GET.get("filter_by")
    sort_by = request.GET.get("sort_by", "score")
    sort_order = request.GET.get("sort_order", "desc")
    page_number = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 25))
    teacher_mode = request.GET.get("teacher_mode") == "1" or teacher is not None

    departments = Department.objects.all().order_by("name")
    sections = []
    limit_to_students = None

    if teacher_mode and teacher:
        handled_sections = teacher.handled_sections.select_related("year_level", "section", "department")

        # Get all handled section IDs
        all_handled_section_ids = [hs.section.id for hs in handled_sections]

        # Now filter only if a department is selected
        if department_name and department_name.lower() != "all":
            filtered_section_ids = [
                hs.section.id for hs in handled_sections if hs.department.name == department_name
            ]
        else:
            filtered_section_ids = all_handled_section_ids

        # Fetch all sections for the teacher's handled sections
        sections = Section.objects.filter(id__in=filtered_section_ids).select_related('year_level') \
            .order_by('year_level__year', 'letter')

    else:
        # Admin mode: Fetch sections for the selected department or all sections
        if department_name and department_name.lower() != "all":
            sections = Section.objects.filter(department__name=department_name) \
                .select_related("year_level").order_by("year_level__year", "letter")
        else:
            sections = Section.objects.select_related("year_level").order_by("year_level__year", "letter")

    # Remove duplicates based on year_level and letter for both teacher and admin modes
    unique_sections = []
    seen = set()
    for section in sections:
        section_key = (section.year_level.id, section.letter)
        if section_key not in seen:
            seen.add(section_key)
            unique_sections.append(section)

    sections = unique_sections  # Now `sections` will contain unique values

    # Rankings limited to teacher's handled students in teacher mode
    if teacher_mode and teacher:
        limit_to_students = Student.objects.filter(
            section__id__in=filtered_section_ids
        ).values_list('id', flat=True)

    rankings = get_all_student_rankings(
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by=section_filter,
        department_filter=None if department_name and department_name.lower() == "all" else department_name,
        limit_to_students=limit_to_students  # 🔒 always in teacher mode
    )

    paginator = Paginator(rankings, per_page)
    page_obj = paginator.get_page(page_number)

    return {
        'departments': departments,
        'sections': sections,
        'rankings': page_obj.object_list,
        'page_obj': page_obj,
        'selected_department': department_name,
        'selected_section': section_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'per_page': per_page,
        'teacher_mode': teacher_mode,
    }
