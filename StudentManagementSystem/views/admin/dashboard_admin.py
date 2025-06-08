from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from GameProgress.services.ranking import get_all_student_rankings
from StudentManagementSystem.models import SimpleAdmin, Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel


def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    storage = messages.get_messages(request)
    list(storage)

    try:
        admin = SimpleAdmin.objects.get(id=admin_id)
    except SimpleAdmin.DoesNotExist:
        messages.error(request, 'Admin account not found.')
        return redirect('admin_login')

    departments = Department.objects.all()
    sections = Section.objects.all()
    rankings = get_all_student_rankings()

    return render(request, 'admin/dashboard.html', {
        'admin': admin,
        'departments': departments,
        'sections': sections,
        'rankings': rankings,
    })

def create_teacher(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        raw_password = request.POST.get('password')
        department_ids = request.POST.getlist('departments[]')
        section_ids = request.POST.getlist('section_ids[]')

        # Validate fields
        if not teacher_id or not raw_password or not department_ids or not section_ids:
            messages.error(request, 'Please fill in all fields.')
            return redirect('admin_dashboard')

        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists.')
            return redirect('admin_dashboard')

        # Try to get or create YearLevel with year=1
        try:
            year_level = YearLevel.objects.get(year=1)
        except YearLevel.DoesNotExist:
            year_level = YearLevel.objects.create(year=1)

        try:
            # Create teacher
            hashed_password = make_password(raw_password)
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                password=hashed_password
            )

            labels = []

            # Match dept[i] ↔ section[i]
            for dept_id, sec_id in zip(department_ids, section_ids):
                department = Department.objects.get(id=dept_id)
                section = Section.objects.get(id=sec_id)

                HandledSection.objects.create(
                    teacher=teacher,
                    department=department,
                    year_level=year_level,
                    section=section
                )

                labels.append(f"{department.name}{year_level.year}{section.letter}")

            messages.success(request, f'Teacher \"{teacher_id}\" assigned to: {', '.join(labels)}')

        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}')

    return redirect('admin_dashboard')