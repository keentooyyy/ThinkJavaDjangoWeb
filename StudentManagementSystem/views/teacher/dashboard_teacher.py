from django.shortcuts import render, redirect
from StudentManagementSystem.models import Teacher
from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.ranking import get_all_student_rankings

def get_teacher_dashboard_context(teacher):
    handled_sections = teacher.handled_sections.select_related('department', 'year_level', 'section')

    return {
        'teacher': teacher,
        'rankings': get_all_student_rankings(sort_by="score", sort_order="desc"),
        'sections_handled': [
            f"{hs.department.name}{hs.year_level.year}{hs.section.letter}"
            for hs in handled_sections
        ],
        'handled_sections': handled_sections,
        'level_options': [
            {"value": level.name, "label": level.name}
            for level in LevelDefinition.objects.all()
        ],
        'achievement_options': [
            {
                "value": ach.code,
                "label": ach.title,
                "is_active": ach.is_active  # ✅ Include this
            }
            for ach in AchievementDefinition.objects.all()
        ],
    }

# views/teacher_dashboard.py

def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)
    context = get_teacher_dashboard_context(teacher)
    return render(request, 'teacher/dashboard.html', context)
