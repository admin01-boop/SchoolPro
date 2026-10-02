from django.core.management.base import BaseCommand

from academics.grade_matching import reconcile_enabled_mappings


class Command(BaseCommand):
    help = (
        'Reports whether enabled Years & Levels rows are linked to enrollment GradeLevels.'
    )

    def handle(self, *args, **options):
        summary = reconcile_enabled_mappings()
        self.stdout.write(self.style.SUCCESS(f"{summary['linked']} enabled cell(s) have enrollment grades."))
        for item in summary['unmatched']:
            self.stdout.write(self.style.WARNING(
                f"No enrollment grade is linked to \"{item['label']}\" ({item['track']})."
            ))
