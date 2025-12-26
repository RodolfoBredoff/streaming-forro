from django.contrib import admin
from .models import Course, Module, Lesson

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    inlines = [LessonInline]