from functools import cached_property

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from academics.grade_matching import assignable_grade_level_ids
from academics.labels import format_grade_level_name
from academics.models import AcademicConfiguration, AcademicYear, GradeLevel
from accounts.models import User
from staff.models import AdminProfile, Observer, StaffMember, Teacher
from students.models import EmergencyContact, Enrollment, Guardian, Student, StudentGuardian


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = '__all__'


class StudentGuardianSerializer(serializers.ModelSerializer):
    guardian_detail = GuardianSerializer(source='guardian', read_only=True)

    class Meta:
        model = StudentGuardian
        fields = ['id', 'student', 'guardian', 'guardian_detail', 'relationship', 'is_legal_custody']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    grade_level_display = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = '__all__'

    def get_grade_level_display(self, enrollment):
        if not enrollment.grade_level:
            return None
        return format_grade_level_name(enrollment.grade_level, enrollment.academic_year.grade_numbering_format)

    def validate_grade_level(self, value):
        if value is not None and value.id not in assignable_grade_level_ids():
            raise serializers.ValidationError('This grade level is not enabled in Years & Levels settings.')
        return value

    def validate_curriculum(self, value):
        if value is None:
            return value
        if value.academic_options.filter(is_enabled=True).exists():
            return value
        if self.instance and self.instance.curriculum_id == value.id:
            return value
        raise serializers.ValidationError('This curriculum is not enabled in Key Academic Functions.')


class AdminManagedPasswordFields(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False, validators=[validate_password])
    require_password_change = serializers.BooleanField(write_only=True, required=False)
    must_change_password = serializers.SerializerMethodField()

    def get_must_change_password(self, instance):
        user = self.get_linked_user(instance)
        return bool(user and user.must_change_password)

    def get_linked_user(self, instance):
        return getattr(instance, 'user', None)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if {'password', 'require_password_change'} & attrs.keys():
            request_user = self.context['request'].user
            if not (request_user.is_superuser or request_user.role == User.Role.ADMIN):
                raise PermissionDenied('Only admins may manage user passwords.')
            if not self.get_linked_user(self.instance):
                raise serializers.ValidationError('This record has no linked login account.')
        return attrs

    def update_linked_user_password(self, user, validated_data):
        password = validated_data.pop('password', None)
        require_password_change = validated_data.pop('require_password_change', None)
        if password is None and require_password_change is None:
            return
        if password is not None:
            user.set_password(password)
        user.must_change_password = require_password_change if require_password_change is not None else True
        user.save()


class StudentSerializer(AdminManagedPasswordFields):
    student_guardians = StudentGuardianSerializer(many=True, read_only=True)
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    enrollments = EnrollmentSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not AcademicConfiguration.load().parents_association_enabled:
            data['student_guardians'] = []
        return data

    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'frn', 'full_name', 'khmer_name', 'sex', 'date_of_birth',
            'nationality_1', 'nationality_2', 'remark', 'user',
            'password', 'require_password_change', 'must_change_password',
            'student_guardians', 'emergency_contacts', 'enrollments',
            'created_at', 'updated_at',
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            self.update_linked_user_password(instance.user, validated_data)
            return super().update(instance, validated_data)


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (no nested relations)."""

    grade = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    guardian_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'frn', 'full_name', 'khmer_name', 'sex', 'date_of_birth',
            'grade', 'enrollment_status', 'guardian_count',
        ]

    def _current_enrollment(self, student):
        # Relies on the viewset prefetching `enrollments` (with academic_year/grade_level)
        # so this does not issue an extra query per row.
        current = None
        for enrollment in student.enrollments.all():
            if enrollment.academic_year.is_current:
                current = enrollment
                break
        return current

    def get_grade(self, student):
        enrollment = self._current_enrollment(student)
        if not enrollment or not enrollment.grade_level:
            return None
        return format_grade_level_name(enrollment.grade_level, enrollment.academic_year.grade_numbering_format)

    def get_enrollment_status(self, student):
        enrollment = self._current_enrollment(student)
        return enrollment.get_enrollment_status_display() if enrollment else None

    def get_guardian_count(self, student):
        if not self._parents_enabled:
            return 0
        return len(student.student_guardians.all())

    @cached_property
    def _parents_enabled(self):
        # One query per request instead of one per row (the child serializer is shared across rows).
        return AcademicConfiguration.load().parents_association_enabled


class MyStudentSerializer(StudentListSerializer):
    """A student's own record; omits staff-only fields such as remarks."""

    guardians = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'student_id', 'full_name', 'khmer_name', 'sex', 'date_of_birth',
            'nationality_1', 'nationality_2', 'grade', 'enrollment_status', 'guardians',
        ]

    def get_guardians(self, student):
        if not self._parents_enabled:
            return []
        return [
            {'full_name': link.guardian.full_name, 'relationship': link.get_relationship_display()}
            for link in student.student_guardians.all()
        ]


class RosterProfileSerializer(AdminManagedPasswordFields):
    """Profile fields plus the editable name/e-mail on the linked login user."""

    full_name = serializers.SerializerMethodField()
    first_name = serializers.CharField(source='user.first_name', max_length=150)
    last_name = serializers.CharField(source='user.last_name', max_length=150)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    def get_full_name(self, profile):
        return profile.user.get_full_name() or profile.user.username

    def validate_email(self, value):
        # Email doubles as the login username, so it must stay unique.
        if value and User.objects.filter(username__iexact=value).exclude(pk=self.instance.user_id).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_employee_id(self, value):
        # Blank must be stored as NULL so several people can have no ID under the unique constraint.
        return value or None

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        with transaction.atomic():
            self.update_linked_user_password(instance.user, validated_data)
            if user_data:
                for attr, value in user_data.items():
                    setattr(instance.user, attr, value)
                if user_data.get('email'):
                    instance.user.username = user_data['email'].lower()
                instance.user.save()
            return super().update(instance, validated_data)


class RosterTeacherSerializer(RosterProfileSerializer):
    class Meta:
        model = Teacher
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'username', 'email',
            'employee_id', 'hire_date', 'is_active', 'password', 'require_password_change', 'must_change_password',
        ]


class RosterStaffSerializer(RosterProfileSerializer):
    class Meta:
        model = StaffMember
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'username', 'email',
            'employee_id', 'hire_date', 'job_title', 'department', 'is_active',
            'password', 'require_password_change', 'must_change_password',
        ]


class RosterObserverSerializer(RosterProfileSerializer):
    class Meta:
        model = Observer
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'username', 'email',
            'organization', 'phone', 'is_active', 'password', 'require_password_change', 'must_change_password',
        ]


class RosterParentSerializer(AdminManagedPasswordFields):
    email = serializers.SerializerMethodField()
    has_login = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Guardian
        fields = [
            'id', 'full_name', 'email', 'phone_1', 'phone_2', 'has_login', 'children',
            'password', 'require_password_change', 'must_change_password',
        ]

    def get_linked_user(self, instance):
        return instance.user

    def update(self, instance, validated_data):
        with transaction.atomic():
            self.update_linked_user_password(instance.user, validated_data)
            return super().update(instance, validated_data)

    def get_email(self, guardian):
        return guardian.user.email if guardian.user else ''

    def get_has_login(self, guardian):
        return guardian.user_id is not None

    def get_children(self, guardian):
        return [
            {'student_id': link.student_id, 'full_name': link.student.full_name, 'relationship': link.relationship}
            for link in guardian.student_guardians.all()
        ]


class RosterAdminSerializer(RosterProfileSerializer):
    class Meta:
        model = AdminProfile
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'username', 'email',
            'employee_id', 'job_title', 'phone', 'is_active', 'password', 'require_password_change',
            'must_change_password',
        ]


class RosterUserCreateSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=[
        User.Role.STUDENT,
        User.Role.TEACHER,
        User.Role.STAFF,
        User.Role.PARENT,
        User.Role.OBSERVER,
        User.Role.ADMIN,
    ])
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    ui_language = serializers.ChoiceField(choices=User.Language.choices, default=User.Language.ENGLISH)
    student_id = serializers.CharField(max_length=20, required=False, allow_blank=True)
    sex = serializers.ChoiceField(choices=Student.Sex.choices, required=False)
    date_of_birth = serializers.DateField(required=False)
    grade_level = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), required=False, allow_null=True,
    )
    parent_ids = serializers.PrimaryKeyRelatedField(
        queryset=Guardian.objects.all(), many=True, required=False,
    )
    send_welcome_email = serializers.BooleanField(default=True)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, data):
        if data['user_type'] == User.Role.STUDENT:
            if not data.get('student_id'):
                raise serializers.ValidationError({'student_id': 'Student ID is required for students.'})
            if Student.objects.filter(student_id=data['student_id']).exists():
                raise serializers.ValidationError({'student_id': 'A student with this ID already exists.'})
            if 'sex' not in data:
                raise serializers.ValidationError({'sex': 'Sex is required for students.'})
            if 'date_of_birth' not in data:
                raise serializers.ValidationError({'date_of_birth': 'Date of birth is required for students.'})
            grade_level = data.get('grade_level')
            if grade_level and grade_level.id not in assignable_grade_level_ids():
                raise serializers.ValidationError({
                    'grade_level': 'This grade level is not enabled in Years & Levels settings.',
                })
            if grade_level and not AcademicYear.objects.filter(is_current=True).exists():
                raise serializers.ValidationError({
                    'grade_level': 'Set a current academic year before assigning a year group.',
                })
        if data.get('parent_ids') and not AcademicConfiguration.load().parents_association_enabled:
            raise serializers.ValidationError({'parent_ids': 'Parents Association is currently disabled.'})
        full_name = f"{data['first_name']} {data['last_name']}"
        if len(full_name) > 150:
            raise serializers.ValidationError({'last_name': 'Combined name must be 150 characters or fewer.'})
        return data
