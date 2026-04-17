from django.contrib import admin
from .models import Video, Course, Module, Lesson, WatchProgress, Favorite
from django.db import models
from .widgets import S3ImageWidget

# Isso permite editar Aulas dentro da página do Módulo
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'video', 'order', 'free_preview')

# Isso permite editar Módulos dentro da página do Curso
class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_criacao')
    search_fields = ('titulo',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)} # Preenche o slug automaticamente enquanto você digita o título
    inlines = [ModuleInline]

    # AQUI ESTÁ A MÁGICA:
    # Dizemos ao Django: "Sempre que ver um URLField neste admin, use meu Widget S3"
    formfield_overrides = {
        models.URLField: {'widget': S3ImageWidget},
    }

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'position_seconds', 'completed', 'updated_at')
    list_filter = ('completed',)
    search_fields = ('user__username', 'video__titulo')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'created_at')
    search_fields = ('user__username', 'lesson__title')