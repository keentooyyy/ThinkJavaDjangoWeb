from django.core.management.base import BaseCommand

from GameProgress.services.ranking import get_all_student_rankings


class Command(BaseCommand):
    help = "Show ranked students based on time attack performance and achievements"

    def add_arguments(self, parser):
        parser.add_argument(
            '--sort-by',
            type=str,
            choices=['score', 'time_remaining', 'achievements', 'name', 'section'],
            default='score',
            help=(
                "Sort criteria:\n"
                "  - score: 🧮 total score (time + achievements)\n"
                "  - time_remaining: ⏱️ total remaining time (higher is better)\n"
                "  - achievements: 🏅 most achievements unlocked\n"
                "  - name: 🔤 alphabetical\n"
                "  - section: 🏫 grouped (e.g. CS3A > IT2C)"
            )
        )

        parser.add_argument(
            '--sort-order',
            type=str,
            choices=['asc', 'desc'],
            default='desc',
            help="Sort direction: 'asc' or 'desc' (default: desc)"
        )

        parser.add_argument(
            '--filter-by',
            type=str,
            help="Filter students by section code (e.g., '1A', '3B')"
        )

        parser.add_argument(
            '--department',
            type=str,
            help="Filter students by department name (e.g., 'CS', 'IT')"
        )

    def handle(self, *args, **options):
        sort_by = options['sort_by']
        sort_order = options['sort_order']
        filter_by = options.get('filter_by')
        department = options.get('department')

        rankings = get_all_student_rankings(
            sort_by=sort_by,
            sort_order=sort_order,
            filter_by=filter_by,
            department_filter=department
        )

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
                f"🧮 Score: {student['score']}"
            )

        self.stdout.write("\n✅ Done.")


# # Default (by score descending)
# python manage.py rank_students
#
# # Sort by name A–Z
# python manage.py rank_students --sort-by name --sort-order asc
#
# # Filter to CS students only
# python manage.py rank_students --department CS
#
# # Filter to section CS3A
# python manage.py rank_students --department CS --filter-by 3A
#
# # Sort by achievements descending
# python manage.py rank_students --sort-by achievement