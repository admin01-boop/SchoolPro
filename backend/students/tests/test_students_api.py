from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration, AcademicYear, GradeLevel, YearLevel
from accounts.models import User
from students.models import Enrollment, Guardian, Student, StudentGuardian


class StudentListAPITests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.year_level = YearLevel.objects.create(name='Year 7', order=7)
        self.grade = GradeLevel.objects.create(name='Legacy Year 7 label', order=7, year_level=self.year_level)
        self.student = Student.objects.create(
            student_id='S100', full_name='Jane Roe', sex=Student.Sex.FEMALE, date_of_birth=date(2014, 5, 1),
        )
        Enrollment.objects.create(
            student=self.student, academic_year=self.year, grade_level=self.grade,
            enrollment_status=Enrollment.Status.NEW, start_date=date(2026, 9, 1),
        )
        guardian = Guardian.objects.create(full_name='John Roe')
        StudentGuardian.objects.create(
            student=self.student, guardian=guardian, relationship=StudentGuardian.Relationship.FATHER,
        )

    def test_list_includes_current_grade_status_and_guardian_count(self):
        response = self.client.get('/api/v1/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(r for r in response.data['results'] if r['student_id'] == 'S100')
        self.assertEqual(row['grade'], 'Year 7')
        self.assertEqual(row['enrollment_status'], 'New Enrollment')
        self.assertEqual(row['guardian_count'], 1)

    def test_roster_grade_uses_current_academic_year_format(self):
        self.year.grade_numbering_format = AcademicYear.NumberingFormat.GRADE_11_12
        self.year.save(update_fields=['grade_numbering_format'])

        response = self.client.get('/api/v1/students/')
        row = next(r for r in response.data['results'] if r['student_id'] == 'S100')
        self.assertEqual(row['grade'], 'Grade 6')

    def test_disabled_parent_association_hides_student_guardian_data(self):
        configuration = AcademicConfiguration.load()
        configuration.parents_association_enabled = False
        configuration.save(update_fields=['parents_association_enabled'])

        list_response = self.client.get('/api/v1/students/')
        row = next(r for r in list_response.data['results'] if r['student_id'] == 'S100')
        detail_response = self.client.get(f'/api/v1/students/{self.student.id}/')
        self.assertEqual(row['guardian_count'], 0)
        self.assertEqual(detail_response.data['student_guardians'], [])

    def test_search_by_name(self):
        response = self.client.get('/api/v1/students/', {'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthenticated_denied(self):
        client = APIClient()
        response = client.get('/api/v1/students/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_non_staff_role_denied(self):
        parent = User.objects.create_user(username='parent1', password='Str0ngPass!23', role=User.Role.PARENT)
        client = APIClient()
        client.force_authenticate(parent)
        response = client.get('/api/v1/students/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RosterGradeFilterTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.grade_7 = GradeLevel.objects.create(name='Year 7', order=7)
        self.grade_10 = GradeLevel.objects.create(name='Year 10', order=10)

        self.graded_student = Student.objects.create(
            student_id='S1', full_name='Graded Student', sex=Student.Sex.FEMALE, date_of_birth=date(2014, 1, 1),
        )
        Enrollment.objects.create(
            student=self.graded_student, academic_year=self.year, grade_level=self.grade_7,
            enrollment_status=Enrollment.Status.NEW, start_date=date(2026, 9, 1),
        )
        self.other_grade_student = Student.objects.create(
            student_id='S2', full_name='Other Grade Student', sex=Student.Sex.MALE, date_of_birth=date(2011, 1, 1),
        )
        Enrollment.objects.create(
            student=self.other_grade_student, academic_year=self.year, grade_level=self.grade_10,
            enrollment_status=Enrollment.Status.NEW, start_date=date(2026, 9, 1),
        )
        self.no_grade_student = Student.objects.create(
            student_id='S3', full_name='No Grade Student', sex=Student.Sex.MALE, date_of_birth=date(2015, 1, 1),
        )
        Enrollment.objects.create(
            student=self.no_grade_student, academic_year=self.year, grade_level=None,
            enrollment_status=Enrollment.Status.NEW, start_date=date(2026, 9, 1),
        )

    def test_unfiltered_returns_everyone(self):
        response = self.client.get('/api/v1/students/')
        self.assertEqual(response.data['count'], 3)

    def test_filter_by_grade_excludes_others_and_no_grade(self):
        response = self.client.get('/api/v1/students/', {
            'filter_active': 'true', 'grade_level': self.grade_7.id, 'include_no_grade': 'false',
        })
        names = [row['full_name'] for row in response.data['results']]
        self.assertEqual(names, ['Graded Student'])

    def test_filter_can_include_no_grade_students(self):
        response = self.client.get('/api/v1/students/', {
            'filter_active': 'true', 'grade_level': self.grade_7.id, 'include_no_grade': 'true',
        })
        names = {row['full_name'] for row in response.data['results']}
        self.assertEqual(names, {'Graded Student', 'No Grade Student'})

    def test_filter_with_no_grades_selected_returns_only_no_grade(self):
        response = self.client.get('/api/v1/students/', {'filter_active': 'true', 'include_no_grade': 'true'})
        names = {row['full_name'] for row in response.data['results']}
        self.assertEqual(names, {'No Grade Student'})

