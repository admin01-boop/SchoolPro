from rest_framework import serializers

from academics.labels import format_grade_level_name
from academics.models import (
    AcademicConfiguration,
    AcademicCurriculumOption,
    AcademicYear,
    ClassRoom,
    Curriculum,
    CurriculumFramework,
    CurriculumTrack,
    GradeLevel,
    GradeLevelTrackMapping,
    LeadSource,
    Programme,
    YearLevel,
)


class AcademicConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicConfiguration
        fields = [
            'classes_enabled', 'parents_association_enabled', 'annotations_enabled',
            'term_grade_calculation', 'points_based_averaging', 'year_level_behaviour',
        ]


class AcademicCurriculumOptionSerializer(serializers.ModelSerializer):
    curriculums = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tracks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AcademicCurriculumOption
        fields = [
            'id', 'code', 'provider', 'name', 'order', 'is_enabled', 'is_customizable',
            'short_name', 'full_title', 'curriculums', 'tracks',
        ]


class AcademicCurriculumOptionInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=AcademicCurriculumOption.objects.all())
    is_enabled = serializers.BooleanField()
    short_name = serializers.CharField(allow_blank=True, required=False, default='')
    full_title = serializers.CharField(allow_blank=True, required=False, default='')


class KeyAcademicFunctionsSaveSerializer(serializers.Serializer):
    configuration = AcademicConfigurationSerializer()
    curricula = AcademicCurriculumOptionInputSerializer(many=True)


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'


class CurriculumSerializer(serializers.ModelSerializer):
    academic_options = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=AcademicCurriculumOption.objects.filter(is_enabled=True),
        required=False,
    )

    class Meta:
        model = Curriculum
        fields = ['id', 'name', 'academic_options']

    def validate(self, attrs):
        selected_options = attrs.get('academic_options')
        if selected_options is None and self.instance:
            return attrs
        if not selected_options:
            raise serializers.ValidationError({'academic_options': 'Choose at least one enabled academic curriculum.'})
        return attrs


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = '__all__'


class GradeLevelSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = GradeLevel
        fields = ['id', 'name', 'order', 'year_level', 'display_name']

    def get_display_name(self, grade_level):
        request = self.context.get('request')
        academic_year_id = request.query_params.get('academic_year') if request else None
        academic_year = None
        if academic_year_id:
            academic_year = AcademicYear.objects.filter(pk=academic_year_id).first()
        if academic_year is None:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
        numbering_format = (
            academic_year.grade_numbering_format if academic_year
            else AcademicYear.NumberingFormat.YEAR_12_13
        )
        return format_grade_level_name(grade_level, numbering_format)


class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = '__all__'


class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = '__all__'


class YearLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearLevel
        fields = '__all__'


class CurriculumTrackSerializer(serializers.ModelSerializer):
    academic_option_enabled = serializers.SerializerMethodField()

    class Meta:
        model = CurriculumTrack
        fields = ['id', 'framework', 'academic_option', 'academic_option_enabled', 'name', 'order']

    def get_academic_option_enabled(self, track):
        return track.academic_option.is_enabled if track.academic_option_id else True


class CurriculumFrameworkSerializer(serializers.ModelSerializer):
    tracks = CurriculumTrackSerializer(many=True, read_only=True)

    class Meta:
        model = CurriculumFramework
        fields = ['id', 'name', 'order', 'tracks']


class GradeLevelTrackMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeLevelTrackMapping
        fields = ['id', 'year_level', 'track', 'is_enabled', 'custom_label']


class GradeLevelTrackMappingCellInputSerializer(serializers.Serializer):
    """One cell sent from the frontend when saving the Years & Levels grid."""

    year_level = serializers.IntegerField()
    track = serializers.IntegerField()
    is_enabled = serializers.BooleanField()
    custom_label = serializers.CharField(allow_blank=True, required=False, default='')


class YearsLevelsGridSaveSerializer(serializers.Serializer):
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())
    grade_numbering_format = serializers.ChoiceField(choices=AcademicYear.NumberingFormat.choices)
    mappings = GradeLevelTrackMappingCellInputSerializer(many=True)

