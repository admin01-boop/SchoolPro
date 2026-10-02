"""Seed default Years & Levels grid data (year levels, curriculum frameworks/tracks, cell mappings)."""
from django.core.management.base import BaseCommand

from academics.models import CurriculumFramework, CurriculumTrack, GradeLevelTrackMapping, YearLevel

YEAR_LEVELS = [
    'Nursery', 'EY-1', 'EY-2',
    'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6',
    'Year 7', 'Year 8', 'Year 9', 'Year 10', 'Year 11', 'Year 12', 'Year 13',
]

FRAMEWORKS = {
    'Cambridge Assessment International Education': ['Cambridge Lower Secondary', 'Cambridge IGCSE', 'Cambridge Advanced'],
    'National Curriculum': ['Primary School', 'Middle School', 'High School'],
}


class Command(BaseCommand):
    help = 'Seed default data for the Years & Levels settings grid.'

    def handle(self, *args, **options):
        for order, name in enumerate(YEAR_LEVELS):
            YearLevel.objects.get_or_create(name=name, defaults={'order': order})

        tracks_by_name = {}
        for f_order, (framework_name, track_names) in enumerate(FRAMEWORKS.items()):
            framework, _ = CurriculumFramework.objects.get_or_create(
                name=framework_name, defaults={'order': f_order}
            )
            for t_order, track_name in enumerate(track_names):
                track, _ = CurriculumTrack.objects.get_or_create(
                    framework=framework, name=track_name, defaults={'order': t_order}
                )
                tracks_by_name[track_name] = track

        primary_labels = {
            'Nursery': 'Nursery', 'EY-1': 'K1', 'EY-2': 'K2',
            'Year 1': 'Year 1', 'Year 2': 'Year 2', 'Year 3': 'Year 3',
            'Year 4': 'Year 4', 'Year 5': 'Year 5', 'Year 6': 'Year 6',
        }
        cells = []
        for year_name, label in primary_labels.items():
            cells.append((year_name, 'Primary School', label))
        for n in (7, 8, 9):
            cells.append((f'Year {n}', 'Cambridge Lower Secondary', f'Year {n}'))
            cells.append((f'Year {n}', 'Middle School', f'Year {n}'))
        for n in (10, 11):
            cells.append((f'Year {n}', 'Cambridge IGCSE', f'Year {n}'))
        for n in (10, 11, 12, 13):
            cells.append((f'Year {n}', 'High School', f'Year {n}'))
        for n in (12, 13):
            cells.append((f'Year {n}', 'Cambridge Advanced', f'Year {n}'))

        year_levels_by_name = {yl.name: yl for yl in YearLevel.objects.all()}
        count = 0
        for year_name, track_name, label in cells:
            GradeLevelTrackMapping.objects.update_or_create(
                year_level=year_levels_by_name[year_name],
                track=tracks_by_name[track_name],
                defaults={'is_enabled': True, 'custom_label': label},
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(YEAR_LEVELS)} year levels and {count} grid cells.'))
