from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from pyexpat.errors import messages

from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel


def create_teacher(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        raw_password = request.POST.get('password')
        dept_ids = request.POST.getlist('departments[]')
        letters = request.POST.getlist('letters[]')


        if not teacher_id or not raw_password or not dept_ids or not letters or not first_name or not last_name:
            messages.error(request, 'Please fill in all fields.')
            return redirect('admin_dashboard')

        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists.')
            return redirect('admin_dashboard')

        try:
            hashed_password = make_password(raw_password)
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                first_name=first_name,
                last_name=last_name,
                password=hashed_password,
                date_of_birth=None,
            )

            # Always Year 1 (you can modify to be dynamic later)
            year_level = YearLevel.objects.get_or_create(year=1)[0]
            labels = []

            for dept_id, letter in zip(dept_ids, letters):
                department = Department.objects.get(id=dept_id)

                # Find the actual Section row
                section = Section.objects.get(
                    department=department,
                    year_level=year_level,
                    letter=letter
                )

                HandledSection.objects.create(
                    teacher=teacher,
                    section=section,
                    department=section.department,
                    year_level=section.year_level
                )

                labels.append(f"{section.department.name}{section.year_level.year}{section.letter}")

            messages.success(request, f'Teacher \"{teacher_id}\" assigned to: {', '.join(labels)}')

        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}')

    return redirect('admin_dashboard')


# 1. View to render the teacher list
def teacher_list(request):
    teachers = Teacher.objects.all()  # Get all teachers from the database
    return render(request, 'admin/teacher_list.html', {'teachers': teachers})

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
        'teacher_id': teacher.teacher_id,
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
        'handled_sections': sections_data
    }
    return JsonResponse(data)

# 3. View to handle teacher updates
def edit_teacher(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        raw_password = request.POST.get('password')  # Optional password field

        # Get the teacher object based on the teacher_id
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # Update teacher data
        teacher.first_name = first_name
        teacher.last_name = last_name

        # If password is provided, hash and update it
        if raw_password:
            teacher.password = make_password(raw_password)

        # Save the updated teacher object
        teacher.save()

        # Success message
        messages.success(request, 'Teacher updated successfully.')
        return JsonResponse({'success': True})  # Send a success response

    # If not a POST request, return failure response
    return JsonResponse({'success': False}, status=400)  # Return error if it's not a POST request
