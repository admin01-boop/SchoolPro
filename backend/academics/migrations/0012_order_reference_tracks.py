from django.db import migrations


TRACK_ORDER = {
    'Cambridge Lower Secondary': 10,
    'Cambridge IGCSE': 20,
    'Cambridge Advanced': 30,
    'Cambridge Primary': 40,
    'Primary School': 10,
    'Middle School': 20,
    'High School': 30,
}


def order_reference_tracks(apps, schema_editor):
    CurriculumTrack = apps.get_model('academics', 'CurriculumTrack')
    alias = schema_editor.connection.alias
    for name, order in TRACK_ORDER.items():
        CurriculumTrack.objects.using(alias).filter(name=name).update(order=order)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0011_materialize_academic_curriculum_catalogue'),
    ]

    operations = [
        migrations.RunPython(order_reference_tracks, migrations.RunPython.noop),
    ]
