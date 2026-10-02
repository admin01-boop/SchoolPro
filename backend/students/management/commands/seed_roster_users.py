"""Seed demo parents and students.

Usage:
    python manage.py seed_roster_users [--count 3]

Safe to re-run: users whose seed email already exists are skipped.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from students.models import Guardian
from students.services import create_roster_user

NAMES = [
    ('Sokha', 'Chan'), ('Dara', 'Kim'), ('Srey', 'Pich'), ('Vanna', 'Heng'), ('Rith', 'Sok'),
    ('Sophea', 'Lim'), ('Bopha', 'Touch'), ('Kosal', 'Ly'), ('Maly', 'Chea'), ('Piseth', 'Ouk'),
]
ROLE_ORDER = [
    ('parent', User.Role.PARENT),
    ('student', User.Role.STUDENT),
]


class Command(BaseCommand):
    help = 'Create demo users for every Roster tab role.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=3, help='Users per role (max 10).')

    def handle(self, *args, **options):
        count = max(1, min(options['count'], len(NAMES)))
        acting_user = User.objects.filter(is_superuser=True).first()
        if not acting_user:
            raise CommandError('Create a superuser first (needed to create admin accounts).')

        self.stdout.write(f'{"role":<10}{"username":<28}password')
        for prefix, role in ROLE_ORDER:
            for index in range(count):
                first_name, last_name = NAMES[index]
                email = f'seed.{prefix}{index + 1}@example.test'
                if User.objects.filter(email=email).exists():
                    continue
                data = {
                    'user_type': role,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'ui_language': User.Language.ENGLISH,
                }
                if role == User.Role.STUDENT:
                    data.update(
                        student_id=f'SEED{index + 1:03d}',
                        sex='MALE' if index % 2 == 0 else 'FEMALE',
                        date_of_birth=date(2012 + index % 4, 1, 15),
                        parent_ids=list(Guardian.objects.filter(user__email=f'seed.parent{index + 1}@example.test')),
                    )
                user, _student, password = create_roster_user(data, acting_user)
                self.stdout.write(f'{role:<10}{user.username:<28}{password}')
