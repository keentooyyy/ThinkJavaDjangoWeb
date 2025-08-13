# StudentManagementSystem/views/teacher/edit_teacher.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.roles import Role


@session_login_required(role=Role.TEACHER)
def edit_profile(request, teacher_id):
    # Get the teacher object or return a 404 error if not found
    teacher = get_object_or_404(Teacher, id=teacher_id)

    # Ensure the logged-in teacher can only edit their own profile
    if request.session.get('user_id') != teacher.id:
        messages.error(request, "You can only edit your own profile.")
        return redirect('teacher_dashboard')  # Redirect to the dashboard if it's not the user's profile

    if request.method == 'POST':
        # Update the teacher's data manually using the POST data
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.date_of_birth = request.POST.get('date_of_birth')
        teacher.password = request.POST.get('password')  # You can hash it if needed
        teacher.save()  # Save the updated teacher information
        messages.success(request, "Profile updated successfully!")
        return redirect('teacher_dashboard')  # Redirect to dashboard after successful update

    return render(request, 'teacher/edit_profile.html', {'teacher': teacher})
