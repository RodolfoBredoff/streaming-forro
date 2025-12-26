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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('search_lesson')
        
        if query:
            # Filtra aulas do curso que contenham o nome pesquisado
            context['search_results'] = Lesson.objects.filter(
                module__course=self.object, 
                title__icontains=query
            )
            context['is_searching'] = True
        return context

# Player do vídeo antigo (Mantenha se quiser usar o player individual)
class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video_atual = self.object
        
        # Tentamos encontrar a aula que contém este vídeo
        aula = video_atual.lesson_set.first() 
        
        if aula:
            modulo = aula.module
            # Busca a próxima aula e a anterior no mesmo módulo
            context['proxima_aula'] = modulo.lessons.filter(id__gt=aula.id).order_by('id').first()
            context['aula_anterior'] = modulo.lessons.filter(id__lt=aula.id).order_by('-id').first()
        
        return context

# Upload de Vídeo bruto
class VideoCreateView(LoginRequiredMixin, CreateView):
    model = Video
    fields = ['titulo', 'arquivo']
    template_name = 'core/video_form.html'
    success_url = reverse_lazy('course_list')