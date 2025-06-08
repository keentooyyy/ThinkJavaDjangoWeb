from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from StudentManagementSystem.models import Teacher

def teacher_login(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        raw_password = request.POST.get('password')

        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
            if check_password(raw_password, teacher.password):
                request.session['teacher_id'] = teacher.id
                return redirect('teacher_dashboard')  # adjust as needed
            else:
                messages.error(request, 'Invalid password.')
        except Teacher.DoesNotExist:
            messages.error(request, 'Teacher not found.')

    return render(request, 'teacher/login.html')

def teacher_logout(request):
    request.session.flush()
    return redirect('teacher_login')
