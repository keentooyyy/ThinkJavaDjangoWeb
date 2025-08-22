from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.progress import sync_all_students_with_all_progress
from StudentManagementSystem.views.admin.dashboard_admin import generate_dashboard_context


# Add Level View
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
                # sync_all_students_with_all_progress()  # Sync progress after adding a level
                message_container_id = 'level_message'  # Set message container id for level
            else:
                messages.error(request, f"Level '{level_name}' already exists.")
                message_container_id = 'level_message'  # Set message container id for level

            # Use the context and re-render the admin dashboard
            return redirect('admin_dashboard')

    # If not POST, just re-render the dashboard without changes
    context = generate_dashboard_context(request.session.get('user_id'), None)
    return render(request, 'admin/dashboard.html', context)




def delete_level(request, level_id):
    if request.method == 'POST':
        level = get_object_or_404(LevelDefinition, id=level_id)

        # Delete the level
        level_name = level.name
        level.delete()

        # Sync progress after deleting a level
        # sync_all_students_with_all_progress()

        # Return a JsonResponse to confirm the delete operation
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# Add Achievement View
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
                # sync_all_students_with_all_progress()  # Sync progress after adding an achievement
                message_container_id = 'achievement_message'  # Set message container id for achievement
            else:
                messages.error(request, f"Achievement '{ach_title}' already exists.")
                message_container_id = 'achievement_message'  # Set message container id for achievement

            # Use the context and re-render the admin dashboard
            return redirect('admin_dashboard')

    # If not POST, just re-render the dashboard without changes
    context = generate_dashboard_context(request.session.get('user_id'), None)
    return render(request, 'admin/dashboard.html', context)



def delete_achievement(request, achievement_id):
    if request.method == 'POST':
        achievement = get_object_or_404(AchievementDefinition, id=achievement_id)

        # Delete the achievement
        ach_title = achievement.title
        achievement.delete()

        # Sync progress after deleting an achievement
        # sync_all_students_with_all_progress()

        # Return a JsonResponse to confirm the delete operation
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})









