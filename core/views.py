from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video
from django.views.generic import ListView
from .models import Course

# Lista todos os vídeos (Home)
class VideoListView(LoginRequiredMixin, ListView):
    model = Video
    template_name = 'core/video_list.html'
    context_object_name = 'videos'
    ordering = ['-data_criacao']

# Player do vídeo
class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

# Página de Upload (Caso você ainda use a página customizada)
class VideoCreateView(LoginRequiredMixin, CreateView):
    model = Video
    fields = ['titulo', 'arquivo']
    template_name = 'core/video_form.html'
    success_url = reverse_lazy('video-list')

class CourseListView(ListView):
    model = Course
    template_name = 'core/course_list.html' # O arquivo HTML que vamos criar
    context_object_name = 'courses' # Como chamaremos a lista dentro do HTML

    def get_queryset(self):
        # Retorna apenas os cursos marcados como "Publicado"
        return Course.objects.filter(is_published=True).order_犠by('-created_at')