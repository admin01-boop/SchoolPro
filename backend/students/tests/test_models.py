from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from academics.models import AcademicYear
from students.models import Enrollment, Student


class EnrollmentConstraintTests(TestCase):
    def test_duplicate_enrollment_for_same_year_and_trial_flag_rejected(self):
        student = Student.objects.create(
            student_id='S1', full_name='Test Student', sex=Student.Sex.MALE, date_of_birth=date(2015, 1, 1),
        )
        year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        Enrollment.objects.create(
            student=student, academic_year=year, enrollment_status=Enrollment.Status.NEW,
            start_date=date(2026, 9, 1), is_trial=False,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(
                    student=student, academic_year=year, enrollment_status=Enrollment.Status.NEW,
                    start_date=date(2026, 9, 1), is_trial=False,
                )

