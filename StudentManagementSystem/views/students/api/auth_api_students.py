from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from StudentManagementSystem.models import Student, UserProfile


@csrf_exempt
def api_student_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        #  Accept form-data or x-www-form-urlencoded
        student_id = request.POST.get("student_id")
        password = request.POST.get("password")

        if not student_id or not password:
            return JsonResponse({"error": "Missing student_id or password"}, status=400)

        #  Fetch student
        try:
            student = Student.objects.select_related(
                "section__department", "section__year_level"
            ).get(student_id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({"error": "Student not found"}, status=404)

        #  Verify password
        if not check_password(password, student.password):
            return JsonResponse({"error": "Incorrect password"}, status=401)

        # Get UserProfile
        try:
            profile = UserProfile.objects.get(object_id=student.id, content_type__model="student")
        except UserProfile.DoesNotExist:
            profile = None

        # phone = f"0{profile.phone}"
        # Build response
        section = student.section
        response = {
            "status": "success",
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "role": student.role,
            },
            "section": {
                "dept": section.department.name if section else None,
                "year_level": section.year_level.year if section else None,
                "section_letter": section.letter if section else None,
                "full_section": student.full_section,
            },
            "profile": {
                "middle_initial": profile.middle_initial if profile else None,
                "suffix": profile.suffix if profile else None,
                "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
                "age": profile.age() if profile else None,
                "bio": profile.bio if profile else None,
                "phone": profile.phone if profile else None,
                "father_name": profile.father_name if profile else None,
                "mother_name": profile.mother_name if profile else None,
                "address": {
                    "street": profile.street if profile else None,
                    "barangay": profile.barangay if profile else None,
                    "city": profile.city if profile else None,
                    "province": profile.province if profile else None,
                } if profile else None,
                "profile_picture": request.build_absolute_uri(profile.avatar_url) if (
                            profile and profile.avatar_url) else None,
                "education": [
                    {
                        "institution": edu.institution,
                        "start_year": edu.start_date.year if edu.start_date else None,
                        "graduation_year": edu.graduation_date.year if edu.graduation_date else None,
                    }
                    for edu in profile.educational_backgrounds.all()
                ] if profile else [],
            },
            "test_status": student.test_status,
        }

        return JsonResponse(response, status=200)

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
