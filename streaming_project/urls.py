from django.contrib import admin
from django.urls import path, include # Importante ter o 'include' aqui

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # Isso diz: "use as URLs que estão dentro do app core"
]