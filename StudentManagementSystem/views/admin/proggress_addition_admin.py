from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, get_object_or_404

from GameProgress.models import LevelDefinition, AchievementDefinition
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.logger import create_log
from StudentManagementSystem.views.notifications_helper import create_notification
from StudentManagementSystem.views.sync_all_progress import run_sync_in_background


# Add Level View
@session_login_required(role=Role.ADMIN)
def add_level(request):
    message_tag = 'level_message'
    admin = request.user_obj  # ✅ validated SimpleAdmin

    if request.method == 'POST':
        level_name = request.POST.get('level_name')

        if level_name:
            level, created = LevelDefinition.objects.get_or_create(
                name=level_name
            )

            if created:
                run_sync_in_background()
                messages.success(request, f"Level '{level_name}' has been created successfully.",
                                 extra_tags=message_tag)
                create_log(request, "CREATE", f"Admin {admin.username} created level '{level_name}'.")
            else:
                messages.error(request, f"Level '{level_name}' already exists.", extra_tags=message_tag)
                create_log(request, "UPDATE",
                           f"Admin {admin.username} attempted to create existing level '{level_name}'.")

            return redirect('admin_dashboard')

    return redirect('admin_dashboard')


@session_login_required(role=Role.ADMIN)
def delete_level(request, level_id):
    if request.method == 'POST':
        level = get_object_or_404(LevelDefinition, id=level_id)
        level_name = level.name
        admin = request.user_obj  # ✅ validated SimpleAdmin

        level.delete()
        run_sync_in_background()
        create_log(request, "DELETE", f"Admin {admin.username} deleted level '{level_name}'.")

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# Add Achievement View
@session_login_required(role=Role.ADMIN)
def add_achievement(request):
    message_tag = 'achievement_message'
    admin = request.user_obj  # ✅ validated SimpleAdmin

    if request.method == 'POST':
        ach_code = request.POST.get('achievement_code')
        ach_title = request.POST.get('achievement_title')
        ach_description = request.POST.get('achievement_description')

        if ach_code and ach_title and ach_description:
            achievement, created = AchievementDefinition.objects.get_or_create(
                code=ach_code,
                defaults={'title': ach_title, 'description': ach_description}
            )

            if created:
                run_sync_in_background()
                messages.success(request, f"Achievement '{ach_title}' created.", extra_tags=message_tag)
                create_log(request, "CREATE", f"Admin {admin.username} created achievement '{ach_title}'.")

                # 🔔 Send notification to all teachers
                for teacher in Teacher.objects.all():
                    create_notification(
                        request=request,
                        recipient_role=Role.TEACHER,
                        teacher_recipient=teacher,
                        title="New Achievement Added",
                        message=f"A new achievement '{ach_title}' has been added. Please review it."
                    )

            else:
                messages.error(request, f"Achievement '{ach_title}' already exists.", extra_tags=message_tag)
                create_log(request, "UPDATE",
                           f"Admin {admin.username} attempted to create existing achievement '{ach_title}'.")

            return redirect('admin_dashboard')

    return redirect('admin_dashboard')


@session_login_required(role=Role.ADMIN)
def delete_achievement(request, achievement_id):
    if request.method == 'POST':
        achievement = get_object_or_404(AchievementDefinition, id=achievement_id)
        ach_title = achievement.title
        admin = request.user_obj  # ✅ validated SimpleAdmin

        achievement.delete()
        run_sync_in_background()
        create_log(request, "DELETE", f"Admin {admin.username} deleted achievement '{ach_title}'.")

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@session_login_required(role=Role.ADMIN)
def force_sync_everyone(request):
    message_tag = 'sync_message'
    admin = request.user_obj  # ✅ validated SimpleAdmin

    if request.method == 'POST':
        try:
            run_sync_in_background()
            messages.success(request, 'Everyone synced successfully!', extra_tags=message_tag)
            create_log(request, "UPDATE", f"Admin {admin.username} triggered force sync.")
        except Exception as e:
            messages.error(request, f"Error during sync: {str(e)}", extra_tags=message_tag)
            create_log(request, "ERROR", f"Admin {admin.username} attempted force sync but failed: {str(e)}")
    else:
        messages.error(request, 'Invalid request method.', extra_tags=message_tag)

    return redirect('admin_dashboard')
