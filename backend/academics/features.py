def is_diploma_programme(programme):
    name = programme.name.strip().lower() if programme else ''
    return name == 'dp' or 'diploma programme' in name
