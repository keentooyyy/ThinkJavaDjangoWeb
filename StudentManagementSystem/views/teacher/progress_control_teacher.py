# views/progress_control.py

from django.shortcuts import render, redirect
from django.contrib import messages
from StudentManagementSystem.models import Teacher
from GameProgress.services.progress import (
    sync_all_students_with_all_progress,
    lock_all_levels, unlock_all_levels,
    enable_all_achievements, disable_all_achievements,
    reset_all_progress,
    lock_level, unlock_level,
    set_achievement_active
)
from StudentManagementSystem.views.teacher.dashboard_teacher import get_teacher_dashboard_context


def progress_control_teacher(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        level_name = request.POST.get('level_name')
        achievement_code = request.POST.get('achievement_code')

        if action == 'sync':
            sync_all_students_with_all_progress()
            messages.success(request, "✅ Synced all students with current level and achievement definitions.")
        elif action == 'unlock_levels':
            unlock_all_levels()
            messages.success(request, "✅ All levels have been unlocked.")
        elif action == 'lock_levels':
            lock_all_levels()
            messages.success(request, "🔒 All levels have been locked.")
        elif action == 'enable_achievements':
            enable_all_achievements()
            messages.success(request, "✅ All achievements are now unlockable.")
        elif action == 'disable_achievements':
            disable_all_achievements()
            messages.success(request, "🔒 All achievements are now disabled globally.")
        elif action == 'reset_progress':
            reset_all_progress()
            messages.warning(request, "⚠️ All progress has been reset.")
        elif action == 'lock_single_level' and level_name:
            lock_level(level_name)
            messages.info(request, f"🔒 Level '{level_name}' locked.")
        elif action == 'unlock_single_level' and level_name:
            unlock_level(level_name)
            messages.info(request, f"✅ Level '{level_name}' unlocked.")
        elif action == 'disable_single_achievement' and achievement_code:
            set_achievement_active(achievement_code, False)
            messages.info(request, f"🔒 Achievement '{achievement_code}' is now disabled.")
        elif action == 'enable_single_achievement' and achievement_code:
            set_achievement_active(achievement_code, True)
            messages.info(request, f"✅ Achievement '{achievement_code}' is now unlockable.")

        return redirect('progress_control_teacher')

    context = get_teacher_dashboard_context(teacher)
    context['is_progress_page'] = True
    return render(request, 'teacher/dashboard.html', context)
