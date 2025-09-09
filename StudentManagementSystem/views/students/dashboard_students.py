from django.shortcuts import render, redirect

from GameProgress.services.ranking import get_student_performance
from StudentManagementSystem.models import Student


def student_dashboard(request):
    student_id = request.session.get('user_id')
    if not student_id:
        return redirect('unified_logout')

    try:
        student = Student.objects.get(id=student_id)
        first_name = student.first_name
        last_name = student.last_name

        full_name = f'{first_name} {last_name}'
    except Student.DoesNotExist:
        return redirect('unified_logout')


    performance = get_student_performance(student)
    context = {
        'student': student,
        'performance': performance,
        'username': full_name,
        'role': student.role,
    }
    return render(request, 'students/dashboard.html',context )
