from django.contrib import messages  # Import messages module
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError  # Import IntegrityError for handling database constraints
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from StudentManagementSystem.models import Teacher, SimpleAdmin
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel






def create_teacher(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    admin = SimpleAdmin.objects.get(id=admin_id)
    # Get all departments to display in the select box
    departments = Department.objects.all()

    # Fetch all teachers
    teachers = Teacher.objects.all()

    # If the request method is POST, process the form submission
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
            messages.error(request, 'Please fill in all fields.')
            return redirect('create_teacher')

        # Check if teacher_id already exists
        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists. Please choose a different ID.')
            return redirect('create_teacher')

        # Check if the sections are already handled by another teacher
        for dept_id, letter in zip(dept_ids, letters):
            department = Department.objects.get(id=dept_id)

            # Find the actual Section row
            section = Section.objects.get(department=department, letter=letter)

            # Check if any teacher is already assigned to this section
            if HandledSection.objects.filter(section=section).exists():
                messages.error(request, f'The section {section.department.name}{section.year_level.year}{section.letter} is already assigned to another teacher.')
                return redirect('create_teacher')

        try:
            # Hash the password
            hashed_password = make_password(raw_password)

            # Create the teacher object
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                first_name=first_name,
                last_name=last_name,
                password=hashed_password,
                date_of_birth=None,
            )

            # Default to Year 1 (you can modify to be dynamic later)
            year_level = YearLevel.objects.get_or_create(year=1)[0]
            labels = []

            # Add the teacher's sections
            for dept_id, letter in zip(dept_ids, letters):
                department = Department.objects.get(id=dept_id)

                # Find the actual Section row
                section = Section.objects.get(department=department, year_level=year_level, letter=letter)

                # Create a HandledSection object to link the teacher and section
                HandledSection.objects.create(
                    teacher=teacher,
                    section=section,
                    department=section.department,
                    year_level=section.year_level
                )

                labels.append(f"{section.department.name}{section.year_level.year}{section.letter}")

            messages.success(request, 'Created a teacher successfully!')

        except IntegrityError as e:
            # Handle IntegrityError (like duplicate teacher_id)
            messages.error(request, 'Error: Teacher ID already exists in the database.')
            print(f"IntegrityError: {str(e)}")

        except Exception as e:
            # Catch any other exceptions that occur during teacher creation
            messages.error(request, f'Error creating teacher: {str(e)}')
            print(f"Exception: {str(e)}")

        return redirect('create_teacher')  # Redirect after successful teacher creation

    # If the request method is GET, render the form
    return render(request, 'admin/teacher_form.html', {
        'departments': departments,
        'username': admin.username,
        'role': Role.ADMIN,
        'teachers': teachers,  # Pass the teachers list to the template
    })





# 2. View to fetch teacher details for the modal
def get_teacher_details(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    handled_sections = teacher.handled_sections.all()  # Fetch the handled sections for this teacher

    # Prepare data to send to the frontend
    sections_data = [
        {
            'id': section.id,
            'department': section.department.name,
            'year_level': section.year_level.year,
            'letter': section.section.letter
        }
        for section in handled_sections
    ]

    data = {
        'teacher_id': teacher.id,
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
        'handled_sections': sections_data
    }
    return JsonResponse(data)








def edit_teacher(request, teacher_id):
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
            for dept_id, letter in zip(departments, letters):
                if dept_id and letter:  # Only process if both dept_id and letter are valid
                    try:
                        department = Department.objects.get(id=dept_id)
                        section = Section.objects.get(department=department, letter=letter)

                        # Check if any teacher is already assigned to this section
                        if HandledSection.objects.filter(section=section).exists():
                            # If the section is already handled, show an error message
                            messages.error(request, f"The section {section.department.name}{section.year_level.year}{section.letter} is already assigned to another teacher.")
                            return redirect('edit_teacher', teacher_id=teacher.id)

                        # Create a new handled section for the teacher
                        HandledSection.objects.create(
                            teacher=teacher,
                            section=section,
                            department=department,
                            year_level=section.year_level
                        )
                    except (Department.DoesNotExist, Section.DoesNotExist):
                        # Handle the case where a department or section doesn't exist
                        continue

        return JsonResponse({'success': True})  # Send a success response

    return JsonResponse({'success': False}, status=400)  # Return error if it's not a POST request




















def remove_section(request, section_id):
    if request.method == 'POST':
        # Get the section to be removed
        section = get_object_or_404(HandledSection, id=section_id)

        # Delete the section from the teacher's handled sections
        section.delete()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def delete_teacher(request, teacher_id):
    if request.method == 'DELETE':
        # Get the teacher object based on teacher_id
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # Delete the teacher from the database
        teacher.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)
