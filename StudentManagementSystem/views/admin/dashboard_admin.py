import json

from django.shortcuts import render, redirect

from StudentManagementSystem.models import SimpleAdmin, Teacher
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.views.admin.ranking_students import get_rankings_context


def admin_dashboard(request):
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('unified_login')

    admin = SimpleAdmin.objects.get(id=admin_id)
    ranking_context = get_rankings_context(request)

    # Fetch all teachers
    teachers = Teacher.objects.all()

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
        'teachers': teachers,  # Pass the teachers list to the template
        'sections_by_department': json.dumps(sections_by_department),
        **ranking_context
    })
