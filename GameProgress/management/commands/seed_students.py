import random

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from StudentManagementSystem.models.student import Student
from StudentManagementSystem.models.section import Section
from GameProgress.models.level_definition import LevelDefinition
from GameProgress.models.achievement_definition import AchievementDefinition
from GameProgress.models.level_progress import LevelProgress
from GameProgress.models.achievement_progress import AchievementProgress

from faker import Faker

fake = Faker()


def generate_student_id():
    return f"{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}"


class Command(BaseCommand):
    help = "Seed fake students and their progress using existing sections and definitions"

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=10, help='Number of students to create')

    def handle(self, *args, **options):
        students_to_create = options['students']

        sections = list(Section.objects.select_related('year_level').all())
        if not sections:
            self.stdout.write(self.style.ERROR("❌ No sections found. Please seed sections first."))
            return

        levels = list(LevelDefinition.objects.all())
        achievements = list(AchievementDefinition.objects.all())

        for _ in range(students_to_create):
            student_id = generate_student_id()
            while Student.objects.filter(student_id=student_id).exists():
                student_id = generate_student_id()

            section = random.choice(sections)
            student = Student.objects.create(
                student_id=student_id,
                name=fake.name(),
                password=make_password('123'),
                year_level=section.year_level,
                section=section
            )

            for level in levels:
                LevelProgress.objects.get_or_create(
                    student=student,
                    level=level,
                    defaults={
                        'best_time': random.randint(10, 180),
                        'current_time': random.randint(0, 180)
                    }
                )

            for achievement in achievements:
                AchievementProgress.objects.get_or_create(
                    student=student,
                    achievement=achievement,
                    defaults={'unlocked': random.choice([True, False])}
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Created {students_to_create} students with progress"))
