from django.http.response import JsonResponse

from StudentManagementSystem.models.section import Section


def get_sections_by_department(request):
    department_name = request.GET.get('department', '')

    # Fetch sections associated with the given department
    sections = Section.objects.filter(department__name=department_name).select_related('year_level').values('id',
                                                                                                            'year_level__year',
                                                                                                            'letter')



    # Prepare the section data for the response
    section_data = [
        {
            'id': section['id'],
            'value': f"{section['year_level__year']}{section['letter']}",  # Format: '1A', '2B', etc.
            'label': f"{section['year_level__year']} {section['letter']}"  # Label: '1 A', '2 B', etc.
        }
        for section in sections
    ]

    # Return the section data as a JSON response
    return JsonResponse({'sections': section_data})