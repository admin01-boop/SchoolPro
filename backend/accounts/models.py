from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from simple_history.models import HistoricalRecords


class RoleAwareUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom user supporting the multiple portals (staff/teacher/parent/student)."""

    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Students'
        TEACHER = 'TEACHER', 'Teachers & Advisors'
        PARENT = 'PARENT', 'Parents'
        OBSERVER = 'OBSERVER', 'Observers'
        ADMIN = 'ADMIN', 'Admins'
        STAFF = 'STAFF', 'Staff'

    class Language(models.TextChoices):
        ENGLISH = 'en', 'English'
        KHMER = 'km', 'Khmer'

    # No management access by default; roles that grant it must be chosen explicitly.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OBSERVER)
    ui_language = models.CharField(max_length=5, choices=Language.choices, default=Language.ENGLISH)
    must_change_password = models.BooleanField(default=False)
    objects = RoleAwareUserManager()
    # Never record password hashes or the per-login timestamp in the audit trail.
    history = HistoricalRecords(excluded_fields=['password', 'last_login'])

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
