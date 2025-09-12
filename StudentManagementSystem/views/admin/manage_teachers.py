from django.contrib.auth.hashers import make_password
from django.db import IntegrityError  # Import IntegrityError for handling database constraints
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher, SimpleAdmin
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel
from StudentManagementSystem.views.logger import create_log


def get_teacher_context(admin):
    # admin is already a validated SimpleAdmin instance
    departments = Department.objects.all()
    teachers = Teacher.objects.all()

    teachers_with_sections = []
    for teacher in teachers:
        handled_sections = teacher.handled_sections.all()
        section_names = [str(handled_section.section) for handled_section in handled_sections]
        teachers_with_sections.append({'teacher': teacher, 'section_names': section_names})

    return {
        'departments': departments,
        'username': admin.username,
        'role': Role.ADMIN,
        'teachers_with_sections': teachers_with_sections,
    }





@session_login_required(role=Role.ADMIN)
def create_teacher(request):
    message_tag = 'create_message'
    admin = request.user_obj  # ✅ validated SimpleAdmin

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        raw_password = request.POST.get('password')
        dept_ids = request.POST.getlist('departments[]')
        letters = request.POST.getlist('letters[]')

        if not teacher_id or not raw_password or not dept_ids or not letters or not first_name or not last_name:
            messages.error(request, 'Please fill in all fields.', extra_tags=message_tag)
            return redirect('create_teacher')

        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists.', extra_tags=message_tag)
            return redirect('create_teacher')

        duplicate_sections = []
        for dept_id, letter in zip(dept_ids, letters):
            if dept_id and letter:
                try:
                    department = Department.objects.get(id=dept_id)
                    section = Section.objects.get(department=department, letter=letter)
                    if HandledSection.objects.filter(section=section).exists():
                        duplicate_sections.append(f"{section.department.name}{section.year_level.year}{section.letter}")
                except (Department.DoesNotExist, Section.DoesNotExist):
                    messages.error(request, "Invalid section/department.", extra_tags=message_tag)
                    return redirect('create_teacher')

        if duplicate_sections:
            sections_str = ', '.join(duplicate_sections)
            messages.error(request, f"Sections already assigned: {sections_str}", extra_tags=message_tag)
            return redirect('create_teacher')

        try:
            hashed_password = make_password(raw_password)
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                first_name=first_name,
                last_name=last_name,
                password=hashed_password
            )

            create_log(request, "CREATE", f"Admin {admin.username} created teacher {teacher_id}")

            year_level = YearLevel.objects.get_or_create(year=1)[0]
            for dept_id, letter in zip(dept_ids, letters):
                department = Department.objects.get(id=dept_id)
                section = Section.objects.get(department=department, year_level=year_level, letter=letter)
                HandledSection.objects.create(
                    teacher=teacher, section=section,
                    department=section.department, year_level=section.year_level
                )

            messages.success(request, 'Created teacher successfully!', extra_tags=message_tag)

        except IntegrityError:
            messages.error(request, 'Teacher ID already exists in the database.', extra_tags=message_tag)
        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}', extra_tags=message_tag)

        return redirect('create_teacher')

    context = get_teacher_context(admin)
    return render(request, 'admin/main/teacher_form.html', context)


@session_login_required(role=Role.ADMIN)
def edit_teacher(request, teacher_id):
    message_tag = 'list_message'
    admin = request.user_obj  # ✅ validated SimpleAdmin

    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, id=teacher_id)

        old_first_name, old_last_name, old_password = teacher.first_name, teacher.last_name, teacher.password
        first_name = request.POST.get('first_name_modal')
        last_name = request.POST.get('last_name_modal')
        raw_password = request.POST.get('password_modal')
        departments = request.POST.getlist('departments[]')
        letters = request.POST.getlist('letters[]')

        changes = []
        if first_name and first_name != old_first_name:
            changes.append(f"first name from '{old_first_name}' to '{first_name}'")
            teacher.first_name = first_name
        if last_name and last_name != old_last_name:
            changes.append(f"last name from '{old_last_name}' to '{last_name}'")
            teacher.last_name = last_name
        if raw_password:
            hashed_password = make_password(raw_password)
            if hashed_password != old_password:
                changes.append("password updated")
                teacher.password = hashed_password
        teacher.save()

        new_sections_added, duplicate_sections, sections_to_create = [], [], []
        for dept_id, letter in zip(departments, letters):
            if dept_id and letter:
                try:
                    department = Department.objects.get(id=dept_id)
                    section = Section.objects.get(department=department, letter=letter)
                    if HandledSection.objects.filter(section=section).exists():
                        duplicate_sections.append(f"{section.department.name}{section.year_level.year}{section.letter}")
                    else:
                        sections_to_create.append(section)
                except (Department.DoesNotExist, Section.DoesNotExist):
                    messages.error(request, "Invalid section/department.", extra_tags=message_tag)
                    return redirect('create_teacher')

        if duplicate_sections:
            messages.error(request, f"Sections already assigned: {', '.join(duplicate_sections)}", extra_tags=message_tag)
            return redirect('create_teacher')

        for section in sections_to_create:
            HandledSection.objects.create(
                teacher=teacher, section=section,
                department=section.department, year_level=section.year_level
            )
            new_sections_added.append(f"{section.department.name}{section.year_level.year}{section.letter}")

        log_parts = []
        if changes:
            log_parts.append("updated " + ", ".join(changes))
        if new_sections_added:
            log_parts.append("added section(s): " + ", ".join(new_sections_added))

        if log_parts:
            create_log(
                request, "UPDATE",
                f"Admin {admin.username} has {'; '.join(log_parts)} for teacher {teacher.teacher_id}."
            )

        messages.success(request, 'Teacher details updated successfully!', extra_tags=message_tag)
        return redirect('create_teacher')

    messages.error(request, 'Invalid request method.', extra_tags=message_tag)
    return redirect('create_teacher')




# 2. View to fetch teacher details for the modal
@session_login_required(role=Role.ADMIN)
def get_teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    handled_sections = teacher.handled_sections.all()

    sections_data = [{
        'id': section.id,
        'department': section.department.name,
        'year_level': section.year_level.year,
        'letter': section.section.letter,
        'section_name': f"{section.department.name} {section.year_level.year}{section.section.letter}"
    } for section in handled_sections]

    return JsonResponse({
        'teacher_id': teacher.id,
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
        'handled_sections': sections_data
    })



@session_login_required(role=Role.ADMIN)
def remove_section(request, section_id):
    if request.method == 'POST':
        section = get_object_or_404(HandledSection, id=section_id)
        admin = request.user_obj  # ✅ validated SimpleAdmin

        section.delete()
        create_log(
            request, "DELETE",
            f"Admin {admin.username} removed section {section.department.name}{section.year_level.year}{section.section.letter} "
            f"from teacher {section.teacher.first_name} {section.teacher.last_name}."
        )
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)



@session_login_required(role=Role.ADMIN)
def delete_teacher(request, teacher_id):
    if request.method == 'DELETE':
        teacher = get_object_or_404(Teacher, id=teacher_id)
        admin = request.user_obj  # ✅ validated SimpleAdmin

        teacher.delete()
        create_log(
            request, "DELETE",
            f"Admin {admin.username} deleted teacher {teacher.teacher_id} ({teacher.first_name} {teacher.last_name})."
        )
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)
