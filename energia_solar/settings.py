

import os
from pathlib import Path
import dj_database_url
import environ 


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(DEBUG=(bool, False))

env.read_env(os.path.join(BASE_DIR, '.env')) # <--- Lê o arquivo .env
# --- FIM DA CONFIGURAÇÃO COM DJANGO-ENVIRON --
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
STRIPE_SECRET_KEY = env('SECRET_KEY_STRIPE')
SECRET_KEY=env('SECRET_KEY')

DEFAULT_AI_PROVIDER="gemini"
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') # Certifique-se de definir no ambiente
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') # Certifique-se de definir no ambiente


# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = env('DEBUG', default=False, cast=bool) # <--- Use env()
DEBUG='True'

#ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[]) # <--- Exemplo para ALLOWED_HOSTS
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'solar',
    'produtos',
    'core',
    'pagamento',
    'django_admin_logs',
    'django.contrib.sites',
    'mercadopago',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

]
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',

]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1
LOGIN_URL = 'account_login'
# settings.py
LOGIN_REDIRECT_URL = '/redirecionamento-login/' 
LOGOUT_REDIRECT_URL = 'account_login'
ACCOUNT_LOGOUT_REDIRECT_URL = 'account_login'


ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = True


SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False  
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ROOT_URLCONF = 'energia_solar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR , 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'energia_solar.wsgi.application'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp-mail.outlook.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587) 
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')


# sender = "mauriciodiassilva@hotmail.com"
# password = "EuSouoEuSou01@"  # Replace with your app password

# try:
#     server = smtplib.SMTP("smtp-mail.outlook.com", 587)  # Or 465 if using SSL
#     server.starttls()  # Or server = smtplib.SMTP_SSL("smtp-mail.outlook.com", 465) if using SSL
#     server.login(sender, password)
#     print("Successfully connected to SMTP server.")
# except Exception as e:
#     print(f"Error connecting to SMTP server: {e}")
# finally:
#     server.quit() if server else None


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',pip list
#         'NAME': 'mydb',
#         'USER': 'user',
#         'PASSWORD': 'password',
#         'HOST': 'db',  # mesmo nome do serviço no docker-compose
#         'PORT': '3306',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'), # Usando os.path.join
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF_TRUSTED_ORIGINS = [
#     'https://solarhub.com.br',
#     'https://www.solarhub.com.br',
#     'https://loja.solarhub.com.br',
# ]

CSRF_TRUSTED_ORIGINS = [
    'https://solarhub.com.br',
    'https://www.solarhub.com.br',
    'https://loja.solarhub.com.br',
    'http://127.0.0.1:8000',  # Para desenvolvimento local
    'http://localhost:8000',  # Outra opção comum para desenvolvimento
]
