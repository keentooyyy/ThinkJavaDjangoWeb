from datetime import date
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.helpers.helpers import validate_birthday
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

        # Handle date of birth (allow empty or None)
        dob = request.POST.get('date_of_birth')
        if dob:  # If a date of birth is provided
            dob_date, error_message = validate_birthday(dob)
            if error_message:
                messages.error(request, error_message)
                return render(request, 'teacher/edit_profile.html', {'teacher': teacher})  # Stay on the edit page

            teacher.date_of_birth = dob_date
        else:  # If no date of birth is provided, set it to None or leave unchanged
            teacher.date_of_birth = None

        # Handle password (allow empty or unchanged)
        new_password = request.POST.get('password')
        if new_password:  # If a password is provided, hash and save it
            teacher.password = new_password  # Make sure to hash it before saving, if needed

        teacher.save()  # Save the updated teacher information
        messages.success(request, "Profile updated successfully!")
        return redirect('edit_profile', teacher_id=teacher.id)  # Redirect back to the profile page

    return render(request, 'teacher/edit_profile.html', {'teacher': teacher})
