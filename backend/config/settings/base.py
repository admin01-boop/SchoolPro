"""Settings shared by every environment. SECRET_KEY and DEBUG live in dev.py / prod.py."""

from pathlib import Path

import environ

# backend/ directory (settings/ -> config/ -> backend/).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0'])
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000', 'http://127.0.0.1:3000']
)


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'simple_history',
    'accounts',
    'academics',
    'students',
    'staff',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# Local dev defaults to SQLite. Set DATABASE_URL (e.g. mysql://user:pass@host:3306/dbname)
# in .env to switch to MySQL/MariaDB for staging/production.

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
}

AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = '/api/v1/'


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Phnom_Penh'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_TOKEN_TTL_HOURS = env.int('AUTH_TOKEN_TTL_HOURS', default=12)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Token first: a stale admin session cookie must not force CSRF on token-authenticated calls.
        'accounts.authentication.ExpiringTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'accounts.permissions.IsStaffRole',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='60/min'),
        'user': env('THROTTLE_USER', default='1000/min'),
        'login': env('THROTTLE_LOGIN', default='5/min'),
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 25,
    'EXCEPTION_HANDLER': 'core.exceptions.api_exception_handler',
}

LOG_LEVEL = env('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'},
    },
    'root': {'handlers': ['console'], 'level': LOG_LEVEL},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000', 'http://127.0.0.1:3000']
)

JAZZMIN_SETTINGS = {
    'site_title': 'SISC Admin',
    'site_header': 'Southbridge International School',
    'site_brand': 'SISC School Management',
    'welcome_sign': 'Southbridge International School Cambodia - Admin',
    'copyright': 'Southbridge International School Cambodia',
    'search_model': ['students.Student'],
    'topmenu_links': [
        {'name': 'View Site', 'url': '/admin/', 'permissions': ['auth.view_user']},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'order_with_respect_to': ['students', 'academics', 'accounts', 'auth'],
    'icons': {
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'accounts.User': 'fas fa-user-shield',
        'students.Student': 'fas fa-user-graduate',
        'students.Guardian': 'fas fa-people-roof',
        'students.Enrollment': 'fas fa-clipboard-list',
        'students.EmergencyContact': 'fas fa-phone',
        'academics.AcademicYear': 'fas fa-calendar',
        'academics.Curriculum': 'fas fa-book',
        'academics.Programme': 'fas fa-graduation-cap',
        'academics.GradeLevel': 'fas fa-layer-group',
        'academics.ClassRoom': 'fas fa-chalkboard',
        'academics.LeadSource': 'fas fa-bullhorn',
    },
    'default_icon_parents': 'fas fa-chevron-circle-right',
    'default_icon_children': 'fas fa-circle',
}

JAZZMIN_UI_TWEAKS = {
    'theme': 'flatly',
}


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
