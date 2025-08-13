
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role


@session_login_required(role=Role.STUDENT)
def edit_profile(request, student_id):
    # Get the teacher object or return a 404 error if not found
    student = get_object_or_404(Student, id=student_id)

    # Ensure the logged-in teacher can only edit their own profile
    if request.session.get('user_id') != student.id:
        messages.error(request, "You can only edit your own profile.")
        return redirect('student_dashboard')  # Redirect to the dashboard if it's not the user's profile

    if request.method == 'POST':
        # Update the teacher's data manually using the POST data
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.password = request.POST.get('password')  # You can hash it if needed
        student.save()  # Save the updated teacher information
        messages.success(request, "Profile updated successfully!")
        return redirect('student_dashboard')  # Redirect to dashboard after successful update

    return render(request, 'student/edit_profile.html', {'teacher': student})
