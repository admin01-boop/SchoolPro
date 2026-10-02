from django.contrib import admin

from .models import (
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

admin.site.register(AcademicConfiguration)
admin.site.register(AcademicCurriculumOption)
admin.site.register(AcademicYear)
admin.site.register(Curriculum)
admin.site.register(Programme)
admin.site.register(GradeLevel)
admin.site.register(ClassRoom)
admin.site.register(LeadSource)
admin.site.register(YearLevel)
admin.site.register(CurriculumFramework)
admin.site.register(CurriculumTrack)
admin.site.register(GradeLevelTrackMapping)
