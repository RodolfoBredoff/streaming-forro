import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do arquivo .env com caminho absoluto
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# --- CONFIGURAÇÕES OBRIGATÓRIAS (QUE ESTAVAM FALTANDO) ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
# ---------------------------------------------------------

# ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
ALLOWED_HOSTS = ['34.226.195.5', 'd1qx0sqd14bw8g.cloudfront.net', 'localhost', '127.0.0.1','.compute-1.amazonaws.com',]
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

# --- CONFIGURAÇÃO AWS S3 (IAM ROLE) ---
AWS_STORAGE_BUCKET_NAME = 'streaming-forro-pe-descalco'
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = 'd1qx0sqd14bw8g.cloudfront.net'
AWS_S3_SIGNATURE_VERSION = 's3v4' # OBRIGATÓRIO para evitar erro 400
AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_S3_URL_PROTOCOL = 'https'
AWS_QUERYSTRING_AUTH = True
AWS_DEFAULT_ACL = None

# streaming_project/settings.py

# ... (Mantenha as configurações de AWS_ACCESS_KEY_ID, AWS_STORAGE_BUCKET_NAME, etc, que definimos antes)

# NOVA CONFIGURAÇÃO (Django 4.2+)
# Isso substitui o DEFAULT_FILE_STORAGE e garante que o backend padrão seja o S3
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            # Se quiser, pode passar parâmetros extras aqui, mas os do settings global já resolvem
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Lógica para usar chaves APENAS se existirem, senão usa IAM Role
if os.getenv('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
else:
    # Não definimos as variáveis aqui.
    # O django-storages vai perceber que elas não existem e 
    # deixará o boto3 procurar a IAM Role automaticamente.
    pass 

# Forçar Storage para S3
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Proxy Headers (Necessário para Nginx)SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Configurações de segurança para CSRF e Cabeçalhos de Proxy
CSRF_TRUSTED_ORIGINS = ['https://d1qx0sqd14bw8g.cloudfront.net']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_HTTPONLY = True

# Permite que o upload aconteça via CloudFront sem erro de origem
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000

# 4. ESSENCIAL: Ignorar a verificação de Host do cabeçalho Origin se necessário
SECURE_REFERER_POLICY = 'no-referrer-when-downgrade'

# implementação de view somente no login, O Django agora buscará o nome da rota dentro de accounts/
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'login'