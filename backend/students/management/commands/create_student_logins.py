"""Create logins for students that have none.

Usage:
    python manage.py create_student_logins --domain school.edu [--output logins.csv] [--dry-run]

Username/email is <student_id>@<domain>. Safe to re-run: students that already have a login are skipped.
"""
import csv

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.crypto import get_random_string

from accounts.models import User
from students.models import Student


class Command(BaseCommand):
    help = 'Create logins for students without one and write the initial passwords to a CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--domain', required=True, help='Email domain, e.g. school.edu')
        parser.add_argument('--output', default='student-logins.csv', help='CSV file for the initial passwords.')
        parser.add_argument('--dry-run', action='store_true', help='Report what would be created; change nothing.')

    def handle(self, *args, **options):
        domain = options['domain'].lstrip('@').lower()
        students = Student.objects.filter(user__isnull=True).order_by('student_id')
        rows, skipped = [], 0

        for student in students:
            email = f'{student.student_id}@{domain}'.lower()
            if User.objects.filter(username__iexact=email).exists():
                skipped += 1
                continue
            if options['dry_run']:
                rows.append((student.student_id, email, ''))
                continue
            first_name, _, last_name = student.full_name.partition(' ')
            password = get_random_string(20)
            with transaction.atomic():
                user = User(
                    username=email, email=email, first_name=first_name, last_name=last_name,
                    role=User.Role.STUDENT,
                )
                user.set_password(password)
                user.save()
                student.user = user
                student.save(update_fields=['user'])
            rows.append((student.student_id, email, password))

        if not options['dry_run'] and rows:
            with open(options['output'], 'w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['student_id', 'username', 'initial_password'])
                writer.writerows(rows)

        verb = 'Would create' if options['dry_run'] else 'Created'
        self.stdout.write(f'{verb} {len(rows)} logins; skipped {skipped} (email already in use).')
        if not options['dry_run'] and rows:
            self.stdout.write(f'Initial passwords written to {options["output"]} - hand out, then delete the file.')
