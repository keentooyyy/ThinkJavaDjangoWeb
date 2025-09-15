import random
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from faker import Faker

from GameProgress.models.achievement_definition import AchievementDefinition
from GameProgress.models.achievement_progress import AchievementProgress
from GameProgress.models.level_definition import LevelDefinition
from GameProgress.models.level_progress import LevelProgress
from StudentManagementSystem.models import UserProfile
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.student import Student

fake = Faker()


def generate_student_id():
    return f"{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}"


class Command(BaseCommand):
    help = "Seed fake students and their progress using existing sections and definitions"

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=10, help='Number of students to create')

    def create_student(self, _):
        sections = list(Section.objects.select_related('year_level').all())
        levels = list(LevelDefinition.objects.all())
        achievements = list(AchievementDefinition.objects.all())

        if not sections:
            self.stdout.write(self.style.ERROR("❌ No sections found. Please seed sections first."))
            return

        student_id = generate_student_id()
        while Student.objects.filter(student_id=student_id).exists():
            student_id = generate_student_id()

        section = random.choice(sections)
        student = Student.objects.create(
            student_id=student_id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            password=make_password('123'),
            year_level=section.year_level,
            section=section
        )

        # ✅ Create UserProfile linked via GenericForeignKey
        UserProfile.objects.create(
            content_type=ContentType.objects.get_for_model(Student),
            object_id=student.id,
            date_of_birth=fake.date_of_birth()
        )

        # Create student progress
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

        return f"Created student {student_id}"

    def handle(self, *args, **options):
        students_to_create = options['students']
        self.stdout.write(self.style.SUCCESS(f"Seeding {students_to_create} students..."))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.create_student, _) for _ in range(students_to_create)]

            for future in as_completed(futures):
                self.stdout.write(self.style.SUCCESS(future.result()))

        self.stdout.write(self.style.SUCCESS(f"✅ Created {students_to_create} students with progress"))
