import json

from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from StudentManagementSystem.models import Student


@csrf_exempt  # Required if Unity won't send CSRF token
def api_student_login(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        password = data.get('password')

        if not student_id or not password:
            return JsonResponse({"error": "Missing fields"}, status=400)

        student = Student.objects.get(student_id=student_id)
        if check_password(password, student.password):
            return JsonResponse({
                "status": "success",
                "student_id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "section": str(student.section),  # Optional
                "year_level": str(student.year_level),  # Optional
            })
        else:
            return JsonResponse({"error": "Incorrect password"}, status=401)

    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
