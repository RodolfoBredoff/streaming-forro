from django.contrib import admin
from .models import Video, Course, Module, Lesson


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

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]