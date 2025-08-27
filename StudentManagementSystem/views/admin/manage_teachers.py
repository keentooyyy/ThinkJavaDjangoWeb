from django.contrib.auth.hashers import make_password
from django.db import IntegrityError  # Import IntegrityError for handling database constraints
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher, SimpleAdmin
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel


# @session_login_required(role=Role.ADMIN)
def get_teacher_context(admin_id):
    # Get admin and departments
    admin = SimpleAdmin.objects.get(id=admin_id)
    departments = Department.objects.all()
    teachers = Teacher.objects.all()

    # Prepare list of teachers with their handled sections
    teachers_with_sections = []
    for teacher in teachers:
        handled_sections = teacher.handled_sections.all()

        # Extract section names using __str__ from Section model
        section_names = [str(handled_section.section) for handled_section in handled_sections]

        teachers_with_sections.append({'teacher': teacher, 'section_names': section_names})

    context = {'departments': departments, 'username': admin.username, 'role': Role.ADMIN,
        'teachers_with_sections': teachers_with_sections, }
    return context





@session_login_required(role=Role.ADMIN)
def create_teacher(request):
    # Define the extra_tags variable at the top for easy modification
    message_tag = 'create_message'

    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    if request.method == 'POST':
        # Get form data from the POST request
        teacher_id = request.POST.get('teacher_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        raw_password = request.POST.get('password')
        dept_ids = request.POST.getlist('departments[]')
        letters = request.POST.getlist('letters[]')

        # Ensure all fields are filled
        if not teacher_id or not raw_password or not dept_ids or not letters or not first_name or not last_name:
            messages.error(request, 'Please fill in all fields.', extra_tags=message_tag)
            return redirect('create_teacher')

        # Check if teacher_id already exists
        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists. Please choose a different ID.', extra_tags=message_tag)
            return redirect('create_teacher')

        # Collect duplicate sections that are already assigned to other teachers
        duplicate_sections = []  # List to collect duplicate sections
        for dept_id, letter in zip(dept_ids, letters):
            if dept_id and letter:  # Only process if both dept_id and letter are valid
                try:
                    department = Department.objects.get(id=dept_id)
                    section = Section.objects.get(department=department, letter=letter)

                    # Check if the section is already handled by another teacher
                    if HandledSection.objects.filter(section=section).exists():
                        # If the section is already handled, add it to the duplicate sections list
                        duplicate_sections.append(f"{section.department.name}{section.year_level.year}{section.letter}")
                except (Department.DoesNotExist, Section.DoesNotExist):
                    # Handle the case where a department or section doesn't exist
                    messages.error(request, "One or more sections/departments do not exist. Please try again.",
                                   extra_tags=message_tag)
                    return redirect('create_teacher')

        # If there are any duplicate sections, show an error message with all the duplicates
        if duplicate_sections:
            sections_str = ', '.join(duplicate_sections)
            messages.error(request, f"The section(s) {sections_str} are already assigned to another teacher.",
                           extra_tags=message_tag)
            return redirect('create_teacher')

        try:
            # Hash the password
            hashed_password = make_password(raw_password)

            # Create the teacher object
            teacher = Teacher.objects.create(teacher_id=teacher_id, first_name=first_name, last_name=last_name,
                password=hashed_password, date_of_birth=None, )

            # Default to Year 1 (you can modify to be dynamic later)
            year_level = YearLevel.objects.get_or_create(year=1)[0]

            # Add the teacher's sections
            for dept_id, letter in zip(dept_ids, letters):
                department = Department.objects.get(id=dept_id)
                section = Section.objects.get(department=department, year_level=year_level, letter=letter)

                # Create a HandledSection object to link the teacher and section
                HandledSection.objects.create(teacher=teacher, section=section, department=section.department,
                    year_level=section.year_level)

            messages.success(request, 'Created a teacher successfully!', extra_tags=message_tag)

        except IntegrityError as e:
            messages.error(request, 'Error: Teacher ID already exists in the database.', extra_tags=message_tag)
            print(f"IntegrityError: {str(e)}")

        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}', extra_tags=message_tag)
            print(f"Exception: {str(e)}")

        return redirect('create_teacher')  # Redirect after successful teacher creation

    # Fetch context using the helper function
    context = get_teacher_context(admin_id)
    return render(request, 'admin/teacher_form.html', context)


@session_login_required(role=Role.ADMIN)
def edit_teacher(request, teacher_id):
    # Define the extra_tags variable at the top
    message_tag = 'list_message'

    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    if request.method == 'POST':
        # Get the teacher object based on the teacher_id
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # Get the data from the POST request
        first_name = request.POST.get('first_name_modal')
        last_name = request.POST.get('last_name_modal')
        raw_password = request.POST.get('password_modal')  # Optional password field
        departments = request.POST.getlist('departments[]')  # New departments added
        letters = request.POST.getlist('letters[]')  # New section letters added

        # Update teacher data (first name, last name, and password)
        teacher.first_name = first_name
        teacher.last_name = last_name

        # If password is provided, hash and update it
        if raw_password:
            teacher.password = make_password(raw_password)

        # Save the updated teacher object
        teacher.save()

        # Add new handled sections (department and section) if they don't already exist
        if departments and letters:
            duplicate_sections = []  # List to collect duplicate sections
            sections_to_create = []  # List to store sections to create later

            # First, check if the sections are already handled by another teacher
            for dept_id, letter in zip(departments, letters):
                if dept_id and letter:  # Only process if both dept_id and letter are valid
                    try:
                        department = Department.objects.get(id=dept_id)
                        section = Section.objects.get(department=department, letter=letter)

                        # Check if the section is already handled by another teacher
                        if HandledSection.objects.filter(section=section).exists():
                            # If the section is already handled, add it to the duplicate sections list
                            duplicate_sections.append(
                                f"{section.department.name}{section.year_level.year}{section.letter}")
                        else:
                            # If no duplicate, prepare the section for creation
                            sections_to_create.append(section)

                    except (Department.DoesNotExist, Section.DoesNotExist):
                        # Handle the case where a department or section doesn't exist
                        messages.error(request, "One or more sections/departments do not exist. Please try again.",
                                       extra_tags=message_tag)
                        return redirect('create_teacher')

            # If there are any duplicate sections, show an error message with all the duplicates
            if duplicate_sections:
                sections_str = ', '.join(duplicate_sections)
                messages.error(request, f"The section(s) {sections_str} are already assigned to another teacher.",
                               extra_tags=message_tag)
                return redirect('create_teacher')

            # Now, create all the new handled sections
            for section in sections_to_create:
                HandledSection.objects.create(teacher=teacher, section=section, department=section.department,
                    year_level=section.year_level)

        # On successful update, show a success message and redirect to the dashboard
        messages.success(request, 'Teacher details updated successfully!', extra_tags=message_tag)
        return redirect('create_teacher')

    # Return error if it's not a POST request
    messages.error(request, 'Invalid request method. Please try again.', extra_tags=message_tag)
    return redirect('create_teacher')


# 2. View to fetch teacher details for the modal
@session_login_required(role=Role.ADMIN)
def get_teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    handled_sections = teacher.handled_sections.all()  # Fetch the handled sections for this teacher

    # Prepare data to send to the frontend
    sections_data = [{'id': section.id, 'department': section.department.name, 'year_level': section.year_level.year,
        'letter': section.section.letter,
        'section_name': f"{section.department.name} {section.year_level.year}{section.section.letter}"
        # Combined section name
    } for section in handled_sections]

    data = {'teacher_id': teacher.id, 'first_name': teacher.first_name, 'last_name': teacher.last_name,
        'handled_sections': sections_data}

    return JsonResponse(data)


@session_login_required(role=Role.ADMIN)
def remove_section(request, section_id):
    if request.method == 'POST':
        # Get the section to be removed
        section = get_object_or_404(HandledSection, id=section_id)

        # Delete the section from the teacher's handled sections
        section.delete()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@session_login_required(role=Role.ADMIN)
def delete_teacher(request, teacher_id):
    if request.method == 'DELETE':
        # Get the teacher object based on teacher_id
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # Delete the teacher from the database
        teacher.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)
