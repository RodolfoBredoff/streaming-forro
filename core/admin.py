from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_criacao') # Mostra essas colunas na lista
    search_fields = ('titulo',) # Cria uma barra de busca por título
