from django.shortcuts import redirect

from StudentManagementSystem.models.department import Department
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.student import Student
from StudentManagementSystem.models.year_level import YearLevel


def dummy_login_and_test(request):
    # Randomly select existing department
    department = Department.objects.order_by('?').first()
    if not department:
        raise Exception("No Department found. Please seed the Department table.")

    # Randomly select existing year level
    year_level = YearLevel.objects.order_by('?').first()
    if not year_level:
        raise Exception("No YearLevel found. Please seed the YearLevel table.")

    # Randomly select existing section
    section = Section.objects.order_by('?').first()
    if not section:
        raise Exception("No Section found. Please seed the Section table.")

    # Create or get a dummy student
    student, created = Student.objects.get_or_create(
        name="Dummy Student",
        defaults={
            "department": department,
            "year_level": year_level,
            "section": section,
        }
    )

    if not created:
        student.department = department
        student.year_level = year_level
        student.section = section
        student.save()

    return redirect('get_game_progress', student_id=student.id)
