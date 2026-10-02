from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """Teacher/advisor profile; login identity stays on accounts.User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile',
    )
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()


class StaffMember(models.Model):
    """Non-teaching staff profile; login identity stays on accounts.User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile',
    )
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()


class Observer(models.Model):
    """Observer profile; login identity stays on accounts.User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='observer_profile',
    )
    organization = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()


class AdminProfile(models.Model):
    """Administrator profile; login identity stays on accounts.User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_profile',
    )
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()
