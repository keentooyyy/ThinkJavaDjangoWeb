from django.shortcuts import redirect
from StudentManagementSystem.models.student import Student


def dummy_login_and_test(request):
    student, _ = Student.objects.get_or_create(name="Dummy Student")
    return redirect('get_game_progress', student_id=student.id)
