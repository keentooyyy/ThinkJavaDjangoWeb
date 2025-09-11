from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, get_object_or_404

from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.progress import sync_all_students_with_all_progress
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import SimpleAdmin
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.logger import create_log
from StudentManagementSystem.views.sync_all_progress import run_sync_in_background


# Add Level View

@session_login_required(role=Role.ADMIN)
def add_level(request):
    message_tag = 'level_message'

    if request.method == 'POST':
        level_name = request.POST.get('level_name')
        level_unlocked = request.POST.get('level_unlocked', False) == 'on'

        if level_name:
            level, created = LevelDefinition.objects.get_or_create(
                name=level_name,
                defaults={'unlocked': level_unlocked}
            )

            admin_id = request.session.get('user_id')
            admin = SimpleAdmin.objects.get(id=admin_id)

            if created:
                run_sync_in_background()
                messages.success(
                    request,
                    f"Level '{level_name}' has been created successfully.",
                    extra_tags=message_tag
                )

                # ✅ Log: Creation
                create_log(
                    request,
                    "CREATE",
                    f"Admin {admin.username} created a new level '{level_name}' "
                    f"({'Unlocked' if level_unlocked else 'Locked'} by default)."
                )

            else:
                messages.error(
                    request,
                    f"Level '{level_name}' already exists.",
                    extra_tags=message_tag
                )

                # ✅ Log: Duplicate attempt (optional)
                create_log(
                    request,
                    "UPDATE",
                    f"Admin {admin.username} attempted to create level '{level_name}', "
                    f"but it already exists."
                )

            return redirect('admin_dashboard')

    return redirect('admin_dashboard')


@session_login_required(role=Role.ADMIN)
def delete_level(request, level_id):
    if request.method == 'POST':
        level = get_object_or_404(LevelDefinition, id=level_id)
        level_name = level.name

        # Delete the level
        level.delete()

        # Sync progress after deleting a level
        run_sync_in_background()

        # ✅ Log: Deletion
        admin_id = request.session.get('user_id')
        admin = SimpleAdmin.objects.get(id=admin_id)
        create_log(
            request,
            "DELETE",
            f"Admin {admin.username} deleted the level '{level_name}'."
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# Add Achievement View
@session_login_required(role=Role.ADMIN)
def add_achievement(request):
    message_tag = 'achievement_message'

    if request.method == 'POST':
        ach_code = request.POST.get('achievement_code')
        ach_title = request.POST.get('achievement_title')
        ach_description = request.POST.get('achievement_description')
        ach_is_active = request.POST.get('achievement_is_active', False) == 'on'

        if ach_code and ach_title and ach_description:
            achievement, created = AchievementDefinition.objects.get_or_create(
                code=ach_code,
                defaults={
                    'title': ach_title,
                    'description': ach_description,
                    'is_active': ach_is_active
                }
            )

            admin_id = request.session.get('user_id')
            admin = SimpleAdmin.objects.get(id=admin_id)

            if created:
                run_sync_in_background()
                messages.success(
                    request,
                    f"Achievement '{ach_title}' has been created successfully.",
                    extra_tags=message_tag
                )

                # ✅ Log: Creation
                create_log(
                    request,
                    "CREATE",
                    f"Admin {admin.username} created a new achievement '{ach_title}' "
                    f"(Active: {'Yes' if ach_is_active else 'No'})."
                )

            else:
                messages.error(
                    request,
                    f"Achievement '{ach_title}' already exists.",
                    extra_tags=message_tag
                )

                # ✅ Log: Duplicate attempt
                create_log(
                    request,
                    "UPDATE",
                    f"Admin {admin.username} attempted to create achievement '{ach_title}', "
                    f"but it already exists."
                )

            return redirect('admin_dashboard')

    return redirect('admin_dashboard')


@session_login_required(role=Role.ADMIN)
def delete_achievement(request, achievement_id):
    if request.method == 'POST':
        achievement = get_object_or_404(AchievementDefinition, id=achievement_id)
        ach_title = achievement.title

        # Delete the achievement
        achievement.delete()

        # Sync progress after deleting an achievement
        run_sync_in_background()

        # ✅ Log: Deletion
        admin_id = request.session.get('user_id')
        admin = SimpleAdmin.objects.get(id=admin_id)
        create_log(
            request,
            "DELETE",
            f"Admin {admin.username} deleted the achievement '{ach_title}'."
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)



@session_login_required(role=Role.ADMIN)
def force_sync_everyone(request):
    message_tag = 'sync_message'

    if request.method == 'POST':
        try:
            run_sync_in_background()

            messages.success(request, 'Everyone is synced successfully!', extra_tags=message_tag)

            # ✅ Log: Sync action
            admin_id = request.session.get('user_id')
            admin = SimpleAdmin.objects.get(id=admin_id)
            create_log(
                request,
                "UPDATE",
                f"Admin {admin.username} triggered a force sync for all students."
            )

        except Exception as e:
            messages.error(request, f"Error during sync: {str(e)}", extra_tags=message_tag)

            # ✅ Log: Sync error
            admin_id = request.session.get('user_id')
            admin = SimpleAdmin.objects.get(id=admin_id)
            create_log(
                request,
                "ERROR",
                f"Admin {admin.username} attempted to force sync everyone but failed: {str(e)}"
            )

    else:
        messages.error(request, 'Invalid request method. Please try again.', extra_tags=message_tag)

    return redirect('admin_dashboard')
