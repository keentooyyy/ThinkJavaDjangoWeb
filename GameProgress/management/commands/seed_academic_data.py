from django.core.management.base import BaseCommand

from StudentManagementSystem.models.section import Department, YearLevel, Section


class Command(BaseCommand):
    help = "Seed default departments, year levels, and sections"

    def handle(self, *args, **kwargs):
        # ✅ Usage:
        # python manage.py seed_academic_data
        # Define departments and year levels to seed
        departments = ["CS", "IT"]
        years = [1]  # Add more years if needed
        sections = [chr(c) for c in range(ord("A"), ord("Z") + 1)]  # A-Z sections

        # Seed departments
        for dept_name in departments:
            department, created = Department.objects.get_or_create(name=dept_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Department {dept_name} created."))

        # Seed year levels
        for year in years:
            year_level, created = YearLevel.objects.get_or_create(year=year)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Year Level {year} created."))

        # Seed sections for each department and year level
        for dept_name in departments:
            department = Department.objects.get(name=dept_name)
            for year in years:
                year_level = YearLevel.objects.get(year=year)
                for letter in sections:
                    section_name = f"{dept_name}{year}{letter}"  # Example: CS 1A
                    section, created = Section.objects.get_or_create(
                        department=department,
                        year_level=year_level,
                        letter=letter
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"✅ Section {section_name} created."))

        self.stdout.write(self.style.SUCCESS("✅ Academic seed data successfully inserted."))
