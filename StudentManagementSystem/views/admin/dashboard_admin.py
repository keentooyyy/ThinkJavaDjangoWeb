from django.shortcuts import render, redirect
import json

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect

from StudentManagementSystem.models import SimpleAdmin, Teacher
from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection
from StudentManagementSystem.models.year_level import YearLevel
from StudentManagementSystem.views.admin.ranking_students import get_rankings_context


def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    admin = SimpleAdmin.objects.get(id=admin_id)
    ranking_context = get_rankings_context(request)

    # Build section list grouped by department
    sections_by_department = {}
    for section in Section.objects.select_related('department', 'year_level').all():
        dept_id = section.department.id
        if dept_id not in sections_by_department:
            sections_by_department[dept_id] = []
        sections_by_department[dept_id].append({
            'id': section.id,
            'letter': section.letter
        })

    return render(request, 'admin/dashboard.html', {
        'admin': admin,
        'sections_by_department': json.dumps(sections_by_department),
        **ranking_context
    })
def create_teacher(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        raw_password = request.POST.get('password')
        dept_ids = request.POST.getlist('departments[]')
        letters = request.POST.getlist('letters[]')

        if not teacher_id or not raw_password or not dept_ids or not letters:
            messages.error(request, 'Please fill in all fields.')
            return redirect('admin_dashboard')

        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, 'Teacher ID already exists.')
            return redirect('admin_dashboard')

        try:
            hashed_password = make_password(raw_password)
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                password=hashed_password
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