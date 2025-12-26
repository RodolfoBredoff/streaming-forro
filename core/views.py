from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video, Course, Module, Lesson # Importe todos aqui

# ESTA SERÁ A SUA NOVA HOME (Vitrine de Cursos)
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    login_url = '/accounts/login/'

    def get_queryset(self):
        # Corrigido o caractere estranho no order_by
        return Course.objects.filter(is_published=True).order_by('-created_at')

# Detalhes do Curso (Módulos e Aulas) - Vamos usar esta em breve
class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'
    context_object_name = 'course'

# Player do vídeo antigo (Mantenha se quiser usar o player individual)
class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

# Upload de Vídeo bruto
class VideoCreateView(LoginRequiredMixin, CreateView):
    model = Video
    fields = ['titulo', 'arquivo']
    template_name = 'core/video_form.html'
    success_url = reverse_lazy('course_list')