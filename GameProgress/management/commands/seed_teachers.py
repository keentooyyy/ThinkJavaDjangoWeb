import random
import threading
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from faker import Faker
from concurrent.futures import ThreadPoolExecutor, as_completed

from StudentManagementSystem.models import Teacher
from StudentManagementSystem.models.section import Section
from StudentManagementSystem.models.teachers import HandledSection

fake = Faker()
lock = threading.Lock()  # 🔒 ensures thread safety


def generate_teacher_id():
    return f"{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}"


class Command(BaseCommand):
    help = "Seed fake teachers and their handled sections (unique sections per teacher, some may have none)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--teachers',
            type=int,
            default=10,
            help='Number of teachers to create'
        )

    def create_teacher(self, _, sections_pool):
        # Ensure unique teacher_id
        teacher_id = generate_teacher_id()
        while Teacher.objects.filter(teacher_id=teacher_id).exists():
            teacher_id = generate_teacher_id()

        teacher = Teacher.objects.create(
            teacher_id=teacher_id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            password=make_password('123')
        )

        # 🔒 Safely work with sections_pool
        with lock:
            if sections_pool:
                num_sections = random.randint(0, min(5, len(sections_pool)))  # ✅ allow 0
                assigned_sections = random.sample(sections_pool, num_sections)

                for section in assigned_sections:
                    sections_pool.remove(section)
                    HandledSection.objects.get_or_create(
                        teacher=teacher,
                        department=section.department,
                        year_level=section.year_level,
                        section=section
                    )
                return f"Created teacher {teacher_id} with {len(assigned_sections)} section(s)"
            else:
                return f"Created teacher {teacher_id} with 0 section(s)"

    def handle(self, *args, **options):
        teachers_to_create = options['teachers']
        self.stdout.write(self.style.SUCCESS(f"Seeding {teachers_to_create} teachers..."))

        # Shared pool of all sections
        sections_pool = list(Section.objects.select_related('department', 'year_level').all())
        random.shuffle(sections_pool)

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.create_teacher, _, sections_pool) for _ in range(teachers_to_create)]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    self.stdout.write(self.style.SUCCESS(result))

        self.stdout.write(self.style.SUCCESS(f"✅ Created {teachers_to_create} teachers with unique handled sections"))
