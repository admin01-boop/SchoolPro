from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import AcademicConfiguration, AcademicYear
from accounts.models import User
from accounts.permissions import IsParent, IsStaffRole, IsStudent
from staff.models import AdminProfile, Observer, StaffMember, Teacher
from students import services
from students.models import EmergencyContact, Enrollment, Guardian, Student, StudentGuardian

from .serializers import (
    EmergencyContactSerializer,
    EnrollmentSerializer,
    GuardianSerializer,
    MyStudentSerializer,
    RosterAdminSerializer,
    RosterObserverSerializer,
    RosterParentSerializer,
    RosterStaffSerializer,
    RosterTeacherSerializer,
    RosterUserCreateSerializer,
    StudentGuardianSerializer,
    StudentListSerializer,
    StudentSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.prefetch_related(
        'student_guardians__guardian',
        'emergency_contacts',
        Prefetch('enrollments', queryset=Enrollment.objects.select_related(
            'academic_year', 'grade_level__year_level',
        )),
    ).all()
    filterset_fields = ['sex']
    search_fields = ['full_name', 'khmer_name', 'student_id', 'frn']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('filter_active') != 'true':
            return queryset

        current_grade_level = Enrollment.objects.filter(
            student=OuterRef('pk'), academic_year__is_current=True,
        ).order_by('-start_date').values('grade_level_id')[:1]
        queryset = queryset.annotate(current_grade_level_id=Subquery(current_grade_level))

        grade_level_ids = self.request.query_params.getlist('grade_level')
        include_no_grade = self.request.query_params.get('include_no_grade', 'true') != 'false'

        condition = Q(current_grade_level_id__in=grade_level_ids) if grade_level_ids else Q(pk__in=[])
        if include_no_grade:
            condition |= Q(current_grade_level_id__isnull=True)
        return queryset.filter(condition)


class MyStudentView(APIView):
    """The signed-in student's own record; the student is resolved from the login, never from a URL id."""

    permission_classes = [IsStudent]

    def get(self, request):
        student = Student.objects.filter(user=request.user).prefetch_related(
            'student_guardians__guardian',
            Prefetch('enrollments', queryset=Enrollment.objects.select_related(
                'academic_year', 'grade_level__year_level',
            )),
        ).first()
        if student is None:
            raise NotFound('No student record is linked to this account.')
        return Response(MyStudentSerializer(student).data)


class MyChildrenView(APIView):
    """The signed-in parent's linked students; resolved from the login, never from a URL id."""

    permission_classes = [IsParent]

    def get(self, request):
        if not AcademicConfiguration.load().parents_association_enabled:
            return Response([])
        students = Student.objects.filter(student_guardians__guardian__user=request.user).distinct().prefetch_related(
            'student_guardians__guardian',
            Prefetch('enrollments', queryset=Enrollment.objects.select_related(
                'academic_year', 'grade_level__year_level',
            )),
        )
        return Response(MyStudentSerializer(students, many=True).data)


class RosterProfileViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Lists a role's profile rows and lets management edit them (PATCH only)."""

    permission_classes = [IsStaffRole]
    http_method_names = ['get', 'patch', 'head', 'options']


class RosterTeacherViewSet(RosterProfileViewSet):
    serializer_class = RosterTeacherSerializer
    queryset = Teacher.objects.select_related('user')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id']


class RosterStaffViewSet(RosterProfileViewSet):
    serializer_class = RosterStaffSerializer
    queryset = StaffMember.objects.select_related('user')
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email', 'employee_id', 'job_title', 'department',
    ]


class RosterObserverViewSet(RosterProfileViewSet):
    serializer_class = RosterObserverSerializer
    queryset = Observer.objects.select_related('user')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'organization']


class RosterAdminViewSet(RosterProfileViewSet):
    serializer_class = RosterAdminSerializer
    queryset = AdminProfile.objects.select_related('user')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id', 'job_title']

    def perform_update(self, serializer):
        acting_user = self.request.user
        if not acting_user.is_superuser and acting_user.role != User.Role.ADMIN:
            raise PermissionDenied('Only admins may edit admin accounts.')
        super().perform_update(serializer)


class RosterParentViewSet(RosterProfileViewSet):
    """Lists and edits Guardian rows, including those without a login; not gated by Parents Association."""

    serializer_class = RosterParentSerializer
    queryset = Guardian.objects.select_related('user').prefetch_related('student_guardians__student')
    search_fields = ['full_name', 'phone_1', 'phone_2', 'user__email']


class RosterUserCreateView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request):
        serializer = RosterUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, student, initial_password = services.create_roster_user(data, request.user)
        welcome_email_sent = data['send_welcome_email'] and services.send_welcome_email(user, initial_password)

        response_data = {
            'id': user.id,
            'username': user.username,
            'user_type': user.role,
            'welcome_email_sent': welcome_email_sent,
            'student_id': student.student_id if student else None,
        }
        if not welcome_email_sent:
            response_data['initial_password'] = initial_password
        return Response(response_data, status=status.HTTP_201_CREATED)


class RosterUserOptionsView(APIView):
    permission_classes = [IsStaffRole]

    def get(self, request):
        return Response(services.roster_user_options())


class ParentAssociationFeatureViewSet(viewsets.ModelViewSet):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not AcademicConfiguration.load().parents_association_enabled:
            raise PermissionDenied('Parents Association is disabled in Key Academic Functions.')


class GuardianViewSet(ParentAssociationFeatureViewSet):
    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    search_fields = ['full_name', 'phone_1', 'phone_2']


class StudentGuardianViewSet(ParentAssociationFeatureViewSet):
    queryset = StudentGuardian.objects.select_related('student', 'guardian').all()
    serializer_class = StudentGuardianSerializer
    filterset_fields = ['student', 'guardian', 'relationship']


class EmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.select_related('student').all()
    serializer_class = EmergencyContactSerializer
    filterset_fields = ['student']


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related(
        'student', 'academic_year', 'curriculum', 'programme', 'grade_level__year_level', 'class_room', 'lead_source'
    ).all()
    serializer_class = EnrollmentSerializer
    filterset_fields = ['academic_year', 'is_trial', 'enrollment_status', 'grade_level', 'student']


class RosterFilterOptionsView(APIView):
    """Groups enrollment grade levels by their explicit enabled curriculum mapping."""

    def get(self, request):
        academic_year_id = request.query_params.get('academic_year')
        if academic_year_id:
            academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
        else:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
        return Response(services.roster_filter_options(academic_year))
