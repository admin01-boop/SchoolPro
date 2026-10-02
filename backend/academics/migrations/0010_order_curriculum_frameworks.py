from django.db import migrations


FRAMEWORK_ORDER = {
    'International Baccalaureate': 10,
    'Pearson Edexcel': 20,
    'Cambridge Assessment International Education': 30,
    'International Curriculum Association': 40,
    'The College Board': 50,
    'National Curriculum': 60,
    'International Early Years Curriculum': 70,
}

TRACK_ORDER = {
    'IB Primary Years': 10,
    'IB Middle Years': 20,
    'IB Career-related Programme': 30,
    'IB Diploma': 40,
    'Pearson Edexcel International GCSEs': 10,
    'Pearson BTEC': 20,
    'Pearson Edexcel International Advanced Levels': 30,
    'International Primary Curriculum': 10,
    'International Middle Years Curriculum': 20,
}


def order_curriculum_columns(apps, schema_editor):
    CurriculumFramework = apps.get_model('academics', 'CurriculumFramework')
    CurriculumTrack = apps.get_model('academics', 'CurriculumTrack')
    alias = schema_editor.connection.alias

    for name, order in FRAMEWORK_ORDER.items():
        CurriculumFramework.objects.using(alias).filter(name=name).update(order=order)

    for name, order in TRACK_ORDER.items():
        CurriculumTrack.objects.using(alias).filter(name=name).update(order=order)


def restore_curriculum_order(apps, schema_editor):
    CurriculumFramework = apps.get_model('academics', 'CurriculumFramework')
    CurriculumTrack = apps.get_model('academics', 'CurriculumTrack')
    alias = schema_editor.connection.alias
    for name, order in FRAMEWORK_ORDER.items():
        CurriculumFramework.objects.using(alias).filter(name=name).update(order=order * 10)
    for name, order in TRACK_ORDER.items():
        CurriculumTrack.objects.using(alias).filter(name=name).update(order=order * 10)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0009_classroom_programme'),
    ]

    operations = [
        migrations.RunPython(order_curriculum_columns, restore_curriculum_order),
    ]
