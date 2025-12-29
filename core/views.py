from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video, Course, Module, Lesson
import boto3
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

#(Vitrine de Cursos)
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    login_url = '/accounts/login/'

    def get_queryset(self):
        # Corrigido o caractere estranho no order_by
        return Course.objects.filter(is_published=True).order_by('-created_at')

# Detalhes do Curso (Módulos e Aulas)
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
class VideoCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'core/video_form.html'

@login_required
def get_presigned_url(request):
    # Pegamos o nome e o tipo do arquivo enviados pelo JS
    file_name = request.GET.get('file_name')
    file_type = request.GET.get('file_type')
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    # Geramos os campos necessários para o upload via POST direto
    # Key: caminho onde o arquivo será salvo no S3
    presigned_post = s3_client.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=f"videos/{file_name}",
        Fields={"Content-Type": file_type},
        Conditions=[
            {"Content-Type": file_type},
            ["content-length-range", 0, 524288000] # Limite de 500MB
        ],
        ExpiresIn=3600 # URL expira em 1 hora
    )

    return JsonResponse(presigned_post)

@login_required
def confirm_upload(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        titulo = request.POST.get('titulo') # Pegamos o título do vídeo do JS
        
        # 1. Criamos o objeto Video no banco de dados
        # O campo 'arquivo' no seu modelo Video provavelmente espera um caminho.
        # Como o arquivo já está na pasta 'videos/' no S3, passamos esse caminho.
        novo_video = Video.objects.create(
            titulo=titulo,
            arquivo=f"videos/{file_name}" 
        )
        
        return JsonResponse({
            'status': 'success', 
            'video_id': novo_video.id,
            'message': 'Registro criado com sucesso!'
        })