from django.core.exceptions import ValidationError
from django.db import models, transaction

from .features import is_diploma_programme


class AcademicYear(models.Model):
    """e.g. '2026-2027'."""

    class NumberingFormat(models.TextChoices):
        GRADE_11_12 = 'GRADE_11_12', 'Grade 11 & 12'
        YEAR_12_13 = 'YEAR_12_13', 'Year 12 & 13'

    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    grade_numbering_format = models.CharField(
        max_length=20, choices=NumberingFormat.choices, default=NumberingFormat.YEAR_12_13,
    )

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['is_current'], condition=models.Q(is_current=True),
                name='only_one_current_academic_year',
            ),
        ]

    def save(self, *args, **kwargs):
        # Marking a year current demotes the previous one so the constraint never trips.
        with transaction.atomic():
            if self.is_current:
                AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Curriculum(models.Model):
    """e.g. Cambridge IGCSE, Cambridge Lower Secondary, IEYC."""

    name = models.CharField(max_length=100, unique=True)
    academic_options = models.ManyToManyField(
        'AcademicCurriculumOption', blank=True, related_name='curriculums',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Programme(models.Model):
    """e.g. Integrated Curriculum."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AcademicConfiguration(models.Model):
    class TermGradeCalculation(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'Use Percentage weights'
        ABSOLUTE = 'ABSOLUTE', 'Use Absolute weights'

    class YearLevelBehaviour(models.TextChoices):
        MATCH_GROUP = 'MATCH_GROUP', 'Match Group Year Level'
        MATCH_IF_BLANK = 'MATCH_IF_BLANK', 'Match Group Year Level if Blank'
        PRESERVE = 'PRESERVE', 'Preserve Year Level'

    classes_enabled = models.BooleanField(default=True)
    parents_association_enabled = models.BooleanField(default=True)
    annotations_enabled = models.BooleanField(default=True)
    term_grade_calculation = models.CharField(
        max_length=20, choices=TermGradeCalculation.choices, default=TermGradeCalculation.PERCENTAGE,
    )
    points_based_averaging = models.BooleanField(default=True)
    year_level_behaviour = models.CharField(
        max_length=20, choices=YearLevelBehaviour.choices, default=YearLevelBehaviour.MATCH_GROUP,
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        configuration, _ = cls.objects.get_or_create(pk=1)
        return configuration

    def __str__(self):
        return 'Key Academic Functions'


class AcademicCurriculumOption(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    provider = models.CharField(max_length=120)
    name = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)
    is_enabled = models.BooleanField(default=False)
    is_customizable = models.BooleanField(default=False)
    short_name = models.CharField(max_length=30, blank=True)
    full_title = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.provider}: {self.name}'


class GradeLevel(models.Model):
    """e.g. Nursery, K1-IC, Year 10 (Grade 9)."""

    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0, help_text='Used to sort grade levels for display.')
    year_level = models.ForeignKey(
        'YearLevel', on_delete=models.SET_NULL, null=True, blank=True, related_name='grade_levels',
        help_text='Canonical Years & Levels row used for enrollment display and curriculum availability.',
    )

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    """A class/section within a grade level for a given academic year."""

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classrooms')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='classrooms')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='classrooms')
    english_name = models.CharField(max_length=100)
    khmer_name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['academic_year', 'grade_level', 'english_name']
        unique_together = ('academic_year', 'grade_level', 'english_name')

    def clean(self):
        super().clean()
        configuration = AcademicConfiguration.objects.filter(pk=1).first()
        if not configuration or configuration.classes_enabled:
            return
        if not self.programme_id:
            raise ValidationError({'programme': 'Assign this class to DP before saving it while Classes is disabled.'})
        if is_diploma_programme(self.programme):
            return
        raise ValidationError({'programme': 'Class changes are disabled for all programmes except DP.'})

    def __str__(self):
        return f'{self.english_name} ({self.academic_year})'


class LeadSource(models.Model):
    """How a trial/prospective family learned about the school."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class YearLevel(models.Model):
    """A row in the Years & Levels grid, e.g. Nursery, EY-1, Year 6 - independent of curriculum."""

    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class CurriculumFramework(models.Model):
    """A column group header, e.g. 'Cambridge Assessment International Education'."""

    name = models.CharField(max_length=150, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class CurriculumTrack(models.Model):
    """A single grid column under a framework, e.g. 'Cambridge IGCSE'."""

    framework = models.ForeignKey(CurriculumFramework, on_delete=models.CASCADE, related_name='tracks')
    academic_option = models.ForeignKey(
        'AcademicCurriculumOption', on_delete=models.SET_NULL, null=True, blank=True, related_name='tracks',
    )
    name = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['framework__order', 'order']
        unique_together = ('framework', 'name')

    def __str__(self):
        return f'{self.framework.name} - {self.name}'


class GradeLevelTrackMapping(models.Model):
    """One grid cell: whether a canonical year level is offered on a track, and its optional label."""

    year_level = models.ForeignKey(YearLevel, on_delete=models.CASCADE, related_name='track_mappings')
    track = models.ForeignKey(CurriculumTrack, on_delete=models.CASCADE, related_name='level_mappings')
    is_enabled = models.BooleanField(default=False)
    custom_label = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['year_level__order', 'track__framework__order', 'track__order']
        unique_together = ('year_level', 'track')

    def __str__(self):
        return f'{self.year_level} x {self.track}'



