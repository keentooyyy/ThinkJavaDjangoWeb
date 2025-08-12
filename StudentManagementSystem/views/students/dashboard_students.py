from django.shortcuts import render, redirect

from GameProgress.services.ranking import get_student_performance
from StudentManagementSystem.models import Student


def student_dashboard(request):
    student_id = request.session.get('user_id')
    if not student_id:
        return redirect('unified_login')

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('unified_login')

    performance = get_student_performance(student)
    print(performance)

    return render(request, 'students/dashboard.html', {
        'student': student,
        'performance': performance,
    })
