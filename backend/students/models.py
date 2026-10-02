from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from academics.models import AcademicYear, ClassRoom, Curriculum, GradeLevel, LeadSource, Programme


class Student(models.Model):
    """Static biographical data that does not change year to year."""

    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'

    student_id = models.CharField(max_length=20, unique=True)
    frn = models.CharField('FRN', max_length=20, db_index=True, blank=True, help_text='Family Reference Number - shared by siblings.')
    full_name = models.CharField(max_length=150)
    khmer_name = models.CharField(max_length=150, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices)
    date_of_birth = models.DateField()
    nationality_1 = models.CharField(max_length=50, blank=True)
    nationality_2 = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f'{self.student_id} - {self.full_name}'


class Guardian(models.Model):
    """A parent/guardian, kept separate from Student so siblings share one record."""

    full_name = models.CharField(max_length=150)
    phone_1 = models.CharField(max_length=30, blank=True)
    phone_2 = models.CharField(max_length=30, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='guardian_profile'
    )

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class StudentGuardian(models.Model):
    """Join table linking students to their guardians (father/mother/other)."""

    class Relationship(models.TextChoices):
        FATHER = 'FATHER', 'Father'
        MOTHER = 'MOTHER', 'Mother'
        OTHER = 'OTHER', 'Other'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_guardians')
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='student_guardians')
    relationship = models.CharField(max_length=10, choices=Relationship.choices)
    is_legal_custody = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'guardian', 'relationship')

    def __str__(self):
        return f'{self.guardian} - {self.get_relationship_display()} of {self.student}'


class EmergencyContact(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f'{self.name} ({self.student})'


class Enrollment(models.Model):
    """A student's registration for a given academic year. History lives here, not on Student."""

    class Status(models.TextChoices):
        NEW = 'NEW', 'New Enrollment'
        EXISTING = 'EXISTING', 'Existing'
        RETURNED = 'RETURNED', 'Returned Student'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='enrollments')
    is_trial = models.BooleanField(default=False)
    enrollment_status = models.CharField(max_length=20, choices=Status.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text='Trial "To Date" or withdrawal date.')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    class_room = models.ForeignKey(
        ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments'
    )
    learning_support_programme = models.CharField(max_length=150, blank=True)
    lead_source = models.ForeignKey(
        LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments'
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ['-academic_year', 'student']
        unique_together = ('student', 'academic_year', 'is_trial')

    def __str__(self):
        kind = 'Trial' if self.is_trial else 'Enrollment'
        return f'{kind}: {self.student} - {self.academic_year}'
