import random
import string

from django.shortcuts import redirect
from django.contrib import messages

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section_code import SectionJoinCode
from StudentManagementSystem.models.teachers import HandledSection


# @session_login_required(Role.TEACHER)
def generate_code(section, department, year_level):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    join_code, _ = SectionJoinCode.objects.update_or_create(section=section, department=department,
        year_level=year_level, defaults={'code': code})
    return join_code.code


@session_login_required(role=Role.TEACHER)
def generate_section_code_view(request):
    teacher_id = request.session.get('user_id')

    if not teacher_id or request.method != 'POST':
        return redirect('register_student')

    raw = request.POST.get('section_id')

    try:
        section_id, dept_id, year_id = map(int, raw.split('_'))
    except (ValueError, AttributeError):
        messages.error(request, "Invalid section format.")
        return redirect('register_student')

    handled = HandledSection.objects.filter(teacher_id=teacher_id, section_id=section_id, department_id=dept_id,
        year_level_id=year_id).first()

    if not handled:
        messages.error(request, "You are not assigned to this section.")
        return redirect('register_student')

    code = generate_code(handled.section, handled.department, handled.year_level)
    print(f"code: {code}")

    messages.success(request,
                     f"✅ Code for {handled.department.name}{handled.year_level.year}{handled.section.letter}: <strong>{code}</strong>")
    return redirect('register_student')
