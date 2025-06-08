from django.shortcuts import render, redirect
from GameProgress.services.ranking import get_student_performance
from StudentManagementSystem.models import Student

def student_dashboard(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('student_login')

    performance = get_student_performance(student)

    return render(request, 'students/dashboard.html', {
        'student': student,
        'performance': performance,
    })
