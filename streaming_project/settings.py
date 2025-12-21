import os
from pathlib import Path
from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do arquivo .env
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# Em produção, adicione o IP do seu servidor aqui
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages', # Lib para S3
    'core',     # Seu app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'streaming_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'streaming_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos (CSS, JS do Admin)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

# streaming_project/settings.py

# --- CONFIGURAÇÃO AWS S3 (Modo IAM Role) ---

# 1. Configurações Básicas do Bucket
AWS_STORAGE_BUCKET_NAME = 'streaming-forro-pe-descalco'  # Hardcoded para garantir
AWS_S3_REGION_NAME = 'us-east-1'  # Obrigatório para IAM Role funcionar bem
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')

# 2. Configurações de Arquivo
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_S3_URL_PROTOCOL = 'https:'
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = None  # Importante: Desativa ACLs antigas que o S3 bloqueia

# 3. Limpeza de Credenciais (O Pulo do Gato)
# Definimos explicitamente como None para o boto3 ignorar e buscar a Role da EC2
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None

# 4. Forçar Storage S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# streaming_project/settings.py
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')