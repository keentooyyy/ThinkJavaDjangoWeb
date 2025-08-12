from django.contrib import messages
from django.shortcuts import redirect

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.progress import sync_all_students_with_all_progress


def add_level(request):
    if request.method == 'POST':
        # Add Level
        level_name = request.POST.get('level_name')
        level_unlocked = request.POST.get('level_unlocked', False) == 'on'  # Check if the checkbox is ticked

        if level_name:
            level, created = LevelDefinition.objects.get_or_create(
                name=level_name,
                defaults={'unlocked': level_unlocked}
            )
            if created:
                messages.success(request, f"Level '{level_name}' has been created successfully.")
                sync_all_students_with_all_progress()  # Sync progress after adding a level
            else:
                messages.info(request, f"Level '{level_name}' already exists.")

                # Redirect to the admin dashboard after successful creation
        return redirect('admin_dashboard')

            # If not POST, just redirect back to admin dashboard
    return redirect('admin_dashboard')


def add_achievement(request):
    if request.method == 'POST':
        # Add Achievement
        ach_code = request.POST.get('achievement_code')
        ach_title = request.POST.get('achievement_title')
        ach_description = request.POST.get('achievement_description')
        ach_is_active = request.POST.get('achievement_is_active', False) == 'on'

        if ach_code and ach_title and ach_description:
            achievement, created = AchievementDefinition.objects.get_or_create(
                code=ach_code,
                defaults={'title': ach_title, 'description': ach_description, 'is_active': ach_is_active}
            )
            if created:
                messages.success(request, f"Achievement '{ach_title}' has been created successfully.")
                sync_all_students_with_all_progress()  # Sync progress after adding an achievement
            else:
                messages.info(request, f"Achievement '{ach_title}' already exists.")

        return redirect('admin_dashboard')

            # If not POST, just redirect back to admin dashboard
    return redirect('admin_dashboard')
