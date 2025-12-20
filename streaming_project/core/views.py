from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Video

# Lista todos os vídeos (Home)
class VideoListView(ListView):
    model = Video
    template_name = 'core/video_list.html'
    context_object_name = 'videos'
    ordering = ['-data_criacao']

# Player do vídeo
class VideoDetailView(DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

# Página de Upload
class VideoCreateView(CreateView):
    model = Video
    fields = ['titulo', 'arquivo']
    template_name = 'core/video_form.html'
    success_url = reverse_lazy('video-list')