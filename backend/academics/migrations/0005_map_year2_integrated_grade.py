from django.db import migrations


def map_integrated_year_two(apps, schema_editor):
    GradeLevel = apps.get_model('academics', 'GradeLevel')
    YearLevel = apps.get_model('academics', 'YearLevel')
    alias = schema_editor.connection.alias
    year_two = YearLevel.objects.using(alias).filter(name='Year 2').first()
    if year_two:
        GradeLevel.objects.using(alias).filter(name='Y2-IC', year_level__isnull=True).update(
            year_level_id=year_two.id,
        )


def unmap_integrated_year_two(apps, schema_editor):
    GradeLevel = apps.get_model('academics', 'GradeLevel')
    alias = schema_editor.connection.alias
    GradeLevel.objects.using(alias).filter(name='Y2-IC', year_level__name='Year 2').update(year_level=None)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0004_remove_gradeleveltrackmapping_grade_level_and_more'),
    ]

    operations = [
        migrations.RunPython(map_integrated_year_two, unmap_integrated_year_two),
    ]
