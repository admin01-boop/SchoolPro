from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from academics import services
from academics.features import is_diploma_programme
from academics.labels import format_level_name
from academics.models import (
    AcademicConfiguration,
    AcademicCurriculumOption,
    AcademicYear,
    ClassRoom,
    Curriculum,
    GradeLevel,
    LeadSource,
    Programme,
    YearLevel,
)
from accounts.permissions import IsStaffRole

from .serializers import (
    AcademicConfigurationSerializer,
    AcademicCurriculumOptionSerializer,
    AcademicYearSerializer,
    ClassRoomSerializer,
    CurriculumFrameworkSerializer,
    CurriculumSerializer,
    GradeLevelSerializer,
    KeyAcademicFunctionsSaveSerializer,
    LeadSourceSerializer,
    ProgrammeSerializer,
    YearLevelSerializer,
    YearsLevelsGridSaveSerializer,
)


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer


class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.filter(academic_options__is_enabled=True).distinct()
    serializer_class = CurriculumSerializer


class ProgrammeViewSet(viewsets.ModelViewSet):
    queryset = Programme.objects.all()
    serializer_class = ProgrammeSerializer


class GradeLevelViewSet(viewsets.ModelViewSet):
    queryset = GradeLevel.objects.select_related('year_level').all()
    serializer_class = GradeLevelSerializer


class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.select_related('academic_year', 'grade_level').all()
    serializer_class = ClassRoomSerializer
    filterset_fields = ['academic_year', 'grade_level']

    def _check_class_changes_allowed(self, programme):
        if AcademicConfiguration.load().classes_enabled:
            return
        if is_diploma_programme(programme):
            return
        raise PermissionDenied('Class changes are disabled for all programmes except DP.')

    def perform_create(self, serializer):
        self._check_class_changes_allowed(serializer.validated_data.get('programme'))
        serializer.save()

    def perform_update(self, serializer):
        programme = serializer.validated_data.get('programme', serializer.instance.programme)
        self._check_class_changes_allowed(programme)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_class_changes_allowed(instance.programme)
        instance.delete()


class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.all()
    serializer_class = LeadSourceSerializer


class KeyAcademicFunctionsView(APIView):
    permission_classes = [IsStaffRole]

    def get(self, request):
        configuration = AcademicConfiguration.load()
        curricula = AcademicCurriculumOption.objects.prefetch_related('curriculums', 'tracks').all()
        return Response({
            'configuration': AcademicConfigurationSerializer(configuration).data,
            'curricula': AcademicCurriculumOptionSerializer(curricula, many=True).data,
        })

    def put(self, request):
        serializer = KeyAcademicFunctionsSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.apply_key_academic_functions(serializer.validated_data)
        return self.get(request)


class YearsLevelsGridView(APIView):
    """Backs the Years & Levels settings grid: one GET/PUT for the whole matrix."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        year_levels = YearLevel.objects.all()
        tracks = services.enabled_tracks()
        frameworks = services.enabled_frameworks(tracks)

        requested_year = request.query_params.get('academic_year')
        if requested_year:
            selected_year = get_object_or_404(AcademicYear, pk=requested_year)
        else:
            selected_year = services.default_academic_year()

        stats = services.year_level_stats(selected_year)
        mappings = services.build_grid_mappings(year_levels, tracks, stats)

        return Response({
            'academic_years': AcademicYearSerializer(AcademicYear.objects.all(), many=True).data,
            'selected_academic_year': selected_year.id if selected_year else None,
            'grade_numbering_format': (
                selected_year.grade_numbering_format if selected_year
                else AcademicYear.NumberingFormat.YEAR_12_13
            ),
            'year_levels': [
                {
                    **row,
                    'grade_display_name': format_level_name(
                        row['name'], AcademicYear.NumberingFormat.GRADE_11_12,
                    ),
                }
                for row in YearLevelSerializer(year_levels, many=True).data
            ],
            'frameworks': CurriculumFrameworkSerializer(frameworks, many=True).data,
            'mappings': mappings,
        })

    def put(self, request):
        serializer = YearsLevelsGridSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reconciliation = services.save_years_levels_grid(serializer.validated_data)
        return Response({'reconciliation': reconciliation}, status=status.HTTP_200_OK)
