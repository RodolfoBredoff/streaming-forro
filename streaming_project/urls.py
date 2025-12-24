from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta linha abaixo ativa o Login, Logout e Password Reset
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')), # Conecta o app de vídeos
] 
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)