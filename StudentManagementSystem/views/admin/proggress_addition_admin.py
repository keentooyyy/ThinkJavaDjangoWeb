from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.progress import sync_all_students_with_all_progress


# Add Level View


def add_level(request):
    # Define the extra_tags variable at the top for easy modification
    message_tag = 'level_message'

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
                messages.success(request, f"Level '{level_name}' has been created successfully.",
                                 extra_tags=message_tag)
                # sync_all_students_with_all_progress()  # Sync progress after adding a level
            else:
                messages.error(request, f"Level '{level_name}' already exists.", extra_tags=message_tag)

            # Use the context and re-render the admin dashboard
            return redirect('admin_dashboard')

    # If not POST, just re-render the dashboard without changes
    return redirect('admin_dashboard')


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
    # Define the extra_tags variable at the top for easy modification
    message_tag = 'achievement_message'

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
                messages.success(request, f"Achievement '{ach_title}' has been created successfully.",
                                 extra_tags=message_tag)
                # sync_all_students_with_all_progress()  # Sync progress after adding an achievement
            else:
                messages.error(request, f"Achievement '{ach_title}' already exists.", extra_tags=message_tag)

            # Use the context and re-render the admin dashboard
            return redirect('admin_dashboard')

    # If not POST, just re-render the dashboard without changes
    return redirect('admin_dashboard')


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


def force_sync_everyone(request):
    # Define the extra_tags variable for easy modification
    message_tag = 'sync_message'

    if request.method == 'POST':
        try:
            # Try to sync all students' progress
            sync_all_students_with_all_progress()

            # If successful, show success message
            messages.success(request, 'Everyone is synced successfully!', extra_tags=message_tag)

        except Exception as e:
            # If an error occurs, show error message with the exception message
            messages.error(request, f"Error during sync: {str(e)}", extra_tags=message_tag)

    else:
        # If method is not POST, show an error message
        messages.error(request, 'Invalid request method. Please try again.', extra_tags=message_tag)

    # Redirect to the admin dashboard
    return redirect('admin_dashboard')
