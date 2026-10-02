from django.contrib import admin

from academics.grade_matching import assignable_grade_level_ids
from academics.models import GradeLevel

from .models import EmergencyContact, Enrollment, Guardian, Student, StudentGuardian


class GradeLevelLimitedAdminMixin:
    """Limits the grade_level dropdown to grades enabled via Years & Levels,
    while always keeping any value already assigned on existing enrollments
    selectable so disabling a grade later never breaks existing records."""

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'grade_level':
            ids = assignable_grade_level_ids() | set(
                Enrollment.objects.exclude(grade_level=None).values_list('grade_level_id', flat=True)
            )
            kwargs['queryset'] = GradeLevel.objects.filter(id__in=ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class StudentGuardianInline(admin.TabularInline):
    model = StudentGuardian
    extra = 1


class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1


class EnrollmentInline(GradeLevelLimitedAdminMixin, admin.TabularInline):
    model = Enrollment
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'sex', 'date_of_birth', 'frn')
    search_fields = ('student_id', 'full_name', 'khmer_name', 'frn')
    list_filter = ('sex',)
    inlines = [StudentGuardianInline, EmergencyContactInline, EnrollmentInline]


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_1', 'phone_2')
    search_fields = ('full_name', 'phone_1', 'phone_2')


@admin.register(Enrollment)
class EnrollmentAdmin(GradeLevelLimitedAdminMixin, admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'is_trial', 'enrollment_status', 'grade_level', 'class_room')
    list_filter = ('academic_year', 'is_trial', 'enrollment_status', 'grade_level')
    search_fields = ('student__full_name', 'student__student_id')
