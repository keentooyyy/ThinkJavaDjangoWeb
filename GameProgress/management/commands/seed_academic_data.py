from django.core.management.base import BaseCommand
from StudentManagementSystem.models import Department, YearLevel, Section

class Command(BaseCommand):
    help = "Seed default departments, year levels, and sections"

    def handle(self, *args, **kwargs):
        departments = ["CS", "IT"]
        years = [1, 2, 3, 4]
        sections = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

        for dept_name in departments:
            Department.objects.get_or_create(name=dept_name)

        for year in years:
            YearLevel.objects.get_or_create(year=year)

        for letter in sections:
            Section.objects.get_or_create(letter=letter)

        self.stdout.write(self.style.SUCCESS("✅ Academic seed data successfully inserted."))
