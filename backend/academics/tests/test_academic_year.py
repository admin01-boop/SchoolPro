from django.db import IntegrityError, transaction
from django.test import TestCase

from academics.models import AcademicYear


class AcademicYearCurrentTests(TestCase):
    def test_marking_a_year_current_demotes_the_previous_one(self):
        first = AcademicYear.objects.create(name='2025-2026', is_current=True)
        second = AcademicYear.objects.create(name='2026-2027', is_current=True)

        first.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertTrue(second.is_current)
        self.assertEqual(AcademicYear.objects.filter(is_current=True).count(), 1)

    def test_database_rejects_two_current_years_via_bulk_update(self):
        AcademicYear.objects.create(name='2025-2026', is_current=True)
        other = AcademicYear.objects.create(name='2026-2027', is_current=False)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AcademicYear.objects.filter(pk=other.pk).update(is_current=True)
