from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.exceptions import PermissionDenied

from academics.grade_matching import assignable_grade_level_ids
from academics.labels import format_grade_level_name
from academics.models import AcademicConfiguration, AcademicYear, CurriculumTrack, GradeLevel, GradeLevelTrackMapping
from accounts.models import User

from .models import Enrollment, Guardian, Student, StudentGuardian


def _numbering_format(academic_year):
    return academic_year.grade_numbering_format if academic_year else AcademicYear.NumberingFormat.YEAR_12_13


def _grade_option(grade, numbering_format):
    return {
        'id': grade.id,
        'name': grade.name,
        'display_name': format_grade_level_name(grade, numbering_format),
    }


def create_roster_user(data, acting_user):
    """Create a user plus its student/guardian profile. Returns (user, student, initial_password)."""
    if (
        data['user_type'] == User.Role.ADMIN
        and not acting_user.is_superuser
        and acting_user.role != User.Role.ADMIN
    ):
        raise PermissionDenied('Only admins may create admin accounts.')

    initial_password = get_random_string(20)
    username = data['email'].lower()

    with transaction.atomic():
        user = User(
            username=username,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=username,
            role=data['user_type'],
            ui_language=data['ui_language'],
        )
        user.set_password(initial_password)
        user.save()

        student = None
        if user.role == User.Role.STUDENT:
            student = Student.objects.create(
                student_id=data['student_id'],
                full_name=f'{user.first_name} {user.last_name}',
                sex=data['sex'],
                date_of_birth=data['date_of_birth'],
                user=user,
            )
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            if academic_year:
                Enrollment.objects.create(
                    student=student,
                    academic_year=academic_year,
                    grade_level=data.get('grade_level'),
                    enrollment_status=Enrollment.Status.NEW,
                    start_date=timezone.localdate(),
                )
            for guardian in data.get('parent_ids', []):
                StudentGuardian.objects.get_or_create(
                    student=student,
                    guardian=guardian,
                    relationship=StudentGuardian.Relationship.OTHER,
                )
        elif user.role == User.Role.PARENT:
            Guardian.objects.create(full_name=f'{user.first_name} {user.last_name}', user=user)
        # Teacher, staff, observer and admin profiles are created by staff.signals.

    return user, student, initial_password


def send_welcome_email(user, initial_password):
    """Returns True only if a welcome email was actually sent."""
    if not user.email:
        return False
    default_mailer = getattr(settings, 'MAILERS', {}).get('default', {})
    backend = default_mailer.get('BACKEND') or getattr(
        settings,
        'EMAIL_BACKEND',
        'django.core.mail.backends.smtp.EmailBackend',
    )
    if backend == 'django.core.mail.backends.console.EmailBackend':
        return False
    smtp_options = default_mailer.get('OPTIONS', {})
    smtp_host = smtp_options.get('host') or getattr(settings, 'EMAIL_HOST', '')
    if backend == 'django.core.mail.backends.smtp.EmailBackend' and not smtp_host:
        return False
    try:
        app_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        send_mail(
            'Your school account is ready',
            f'Your username is {user.username}. Your temporary password is {initial_password}. '
            f'Sign in at {app_url}.',
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost'),
            [user.email],
            fail_silently=False,
        )
    except Exception:
        return False
    return True


def roster_user_options():
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    numbering_format = _numbering_format(academic_year)
    assignable_ids = assignable_grade_level_ids() if academic_year else set()
    grade_levels = GradeLevel.objects.filter(id__in=assignable_ids).order_by('order', 'name')
    parents_enabled = AcademicConfiguration.load().parents_association_enabled

    return {
        'academic_year': academic_year.id if academic_year else None,
        'grade_levels': [_grade_option(grade, numbering_format) for grade in grade_levels],
        'parents_enabled': parents_enabled,
        'parents': list(Guardian.objects.values('id', 'full_name')) if parents_enabled else [],
    }


def roster_filter_options(academic_year):
    """Groups assignable grade levels by their explicitly enabled curriculum mapping."""
    numbering_format = _numbering_format(academic_year)
    assignable_ids = assignable_grade_level_ids()
    grade_levels = list(GradeLevel.objects.select_related('year_level').order_by('order', 'name'))
    grades_by_year_level = {}
    for grade in grade_levels:
        if grade.id in assignable_ids and grade.year_level_id:
            grades_by_year_level.setdefault(grade.year_level_id, []).append(grade)
    tracks = CurriculumTrack.objects.select_related('framework').prefetch_related(
        Prefetch(
            'level_mappings',
            queryset=GradeLevelTrackMapping.objects.filter(is_enabled=True).select_related('year_level'),
        ),
    ).filter(academic_option__is_enabled=True).order_by('framework__order', 'order')

    matched_ids = set()
    groups = []
    for track in tracks:
        track_grades = list(dict.fromkeys(
            grade
            for mapping in track.level_mappings.all()
            for grade in grades_by_year_level.get(mapping.year_level_id, [])
        ))
        if not track_grades:
            continue
        matched_ids.update(grade.id for grade in track_grades)
        groups.append({
            'track': track.name,
            'grade_levels': [_grade_option(grade, numbering_format) for grade in track_grades],
        })

    ungrouped = [_grade_option(grade, numbering_format) for grade in grade_levels if grade.id not in matched_ids]
    return {
        'academic_year': academic_year.id if academic_year else None,
        'groups': groups,
        'ungrouped': ungrouped,
    }
