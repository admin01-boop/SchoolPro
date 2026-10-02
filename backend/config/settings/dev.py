from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool('DEBUG', default=True)

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-only-key-do-not-use-in-production')
