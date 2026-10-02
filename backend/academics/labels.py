GRADE_FORMAT_LABELS = {
    'Nursery': 'Pre-K2',
    'EY-1': 'Pre-K3',
    'EY-2': 'Pre-K4',
    'Year 1': 'Kindergarten',
    'Year 2': 'Grade 1',
    'Year 3': 'Grade 2',
    'Year 4': 'Grade 3',
    'Year 5': 'Grade 4',
    'Year 6': 'Grade 5',
    'Year 7': 'Grade 6',
    'Year 8': 'Grade 7',
    'Year 9': 'Grade 8',
    'Year 10': 'Grade 9',
    'Year 11': 'Grade 10',
    'Year 12': 'Grade 11',
    'Year 13': 'Grade 12',
}


def format_level_name(name, numbering_format):
    if numbering_format != 'GRADE_11_12':
        return name

    for year_name, grade_name in GRADE_FORMAT_LABELS.items():
        if name == year_name or name.startswith(f'{year_name} ') or name.startswith(f'{year_name}('):
            return grade_name
    return name


def format_grade_level_name(grade_level, numbering_format):
    canonical_name = grade_level.year_level.name if grade_level.year_level else grade_level.name
    return format_level_name(canonical_name, numbering_format)
