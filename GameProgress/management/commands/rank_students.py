from django.core.management.base import BaseCommand
from GameProgress.services.ranking import get_all_student_rankings

class Command(BaseCommand):
    help = "Show ranked students based on time attack performance and achievements"

    def add_arguments(self, parser):
        # 🧭 Sorting criteria
        parser.add_argument(
            '--sort-by',
            type=str,
            choices=['time_remaining', 'achievements', 'percentage', 'name', 'section'],
            default='time_remaining',
            help=(
                "Sort criteria:\n"
                "  - time_remaining: ⏱️ total remaining time (higher is better)\n"
                "  - achievements: 🏅 most achievements unlocked\n"
                "  - percentage: 📊 percentage of max time preserved\n"
                "  - name: 🔤 alphabetical\n"
                "  - section: 🏫 grouped (e.g. CS3A > IT2C)"
            )
        )

        # 🔄 Ascending/Descending
        parser.add_argument(
            '--sort-order',
            type=str,
            choices=['asc', 'desc'],
            default='desc',
            help="Sort direction: 'asc' or 'desc' (default: desc)"
        )

    def handle(self, *args, **options):
        sort_by = options['sort_by']
        sort_order = options['sort_order']

        rankings = get_all_student_rankings(sort_by=sort_by, sort_order=sort_order)

        if not rankings:
            self.stdout.write("⚠️ No student rankings found.")
            return

        self.stdout.write(f"\n🎓 Student Rankings (sorted by '{sort_by}' in {sort_order.upper()} order):\n")

        for i, student in enumerate(rankings, 1):
            self.stdout.write(
                f"{i:>2}. {student['name']} "
                f"({student['section']}) - "
                f"🕒 Time Left: {student['total_time_remaining']}s | "
                f"🏅 Achievements: {student['achievements_unlocked']} | "
                f"📊 {student['percentage_remaining']}%"
            )

        self.stdout.write("\n✅ Done.")

# -------------------------------------
# 🧪 Usage Examples:
#
# Default:
# python manage.py rank_students
#
# Sort by achievements (descending):
# python manage.py rank_students --sort-by achievements
#
# Sort alphabetically:
# python manage.py rank_students --sort-by name --sort-order asc
#
# Sort from worst performers (least time left):
# python manage.py rank_students --sort-order asc
# -------------------------------------
