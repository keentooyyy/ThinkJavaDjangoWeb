from django.core.management.base import BaseCommand
from GameProgress.services.ranking import get_student_performance
from StudentManagementSystem.models.student import Student

class Command(BaseCommand):
    help = "Show ranking details for a single student by ID only"

    def add_arguments(self, parser):
        parser.add_argument('student_id', type=int, help='Student ID')

    def handle(self, *args, **options):
        student_id = options['student_id']

        try:
            student = Student.objects.get(id=student_id)
            data = get_student_performance(student)

            self.stdout.write(f"\n🎯 Student Performance: {data['name']} ({data['section']})")
            self.stdout.write(f"🆔 ID: {data['student_id']}")
            self.stdout.write(f"🕒 Total Time Remaining: {data['total_time_remaining']}s")
            self.stdout.write(f"🏅 Achievements Unlocked: {data['achievements_unlocked']}")
            self.stdout.write(f"📊 Performance: {data['percentage_remaining']}%")
            self.stdout.write("✅ Done.\n")

        except Student.DoesNotExist:
            self.stderr.write("❌ Student ID not found.")
