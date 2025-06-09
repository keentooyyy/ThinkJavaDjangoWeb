import random
import string
from django.shortcuts import redirect
from django.contrib import messages

from StudentManagementSystem.models.section_code import SectionJoinCode
from StudentManagementSystem.models.teachers import HandledSection


def generate_code(section, department, year_level):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    join_code, _ = SectionJoinCode.objects.update_or_create(
        section=section,
        department=department,
        year_level=year_level,
        defaults={'code': code}
    )
    return join_code.code


def generate_section_code_view(request):
    teacher_id = request.session.get('teacher_id')

    # Print debug to check if teacher_id exists
    print(f"Teacher ID: {teacher_id}")

    if not teacher_id or request.method != 'POST':
        print("No teacher ID or invalid method, redirecting to dashboard.")
        return redirect('teacher_dashboard')

    raw = request.POST.get('section_id')  # Format: sectionID_deptID_yearID
    print(f"Raw section ID: {raw}")

    try:
        section_id, dept_id, year_id = map(int, raw.split('_'))
        print(f"Parsed IDs - Section: {section_id}, Department: {dept_id}, Year Level: {year_id}")
    except (ValueError, AttributeError):
        print("Error in parsing section format.")
        messages.error(request, "Invalid section format.")
        return redirect('teacher_dashboard')

    handled = HandledSection.objects.filter(
        teacher_id=teacher_id,
        section_id=section_id,
        department_id=dept_id,
        year_level_id=year_id
    ).first()

    # Print if handled section is found
    if handled:
        print(f"Handled section found: {handled.section.letter}")
    else:
        print("No handled section found for this teacher.")

    if not handled:
        messages.error(request, "You are not assigned to this section.")
        return redirect('teacher_dashboard')

    code = generate_code(handled.section, handled.department, handled.year_level)
    print(f"Generated code: {code}")

    messages.success(request,
                     f"✅ Code for {handled.department.name}{handled.year_level.year}{handled.section.letter}: <strong>{code}</strong>")
    return redirect('teacher_dashboard')
