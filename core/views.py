from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video, Course, Module, Lesson
import boto3
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from botocore.signers import CloudFrontSigner
import urllib.parse

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

def rsa_signer(message):
    private_key = serialization.load_pem_private_key(
        settings.CLOUDFRONT_PRIVATE_KEY.encode(),
        password=None
    )
    return private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA1()
    )

# Função para gerar a URL assinada
def generate_cloudfront_url(file_path):
    if not file_path:
        return None
    path_quoted = urllib.parse.quote(file_path)

    # Monta a URL base (ex: https://dominio.cloudfront.net/videos/aula.mp4)
    url = f"https://{settings.CLOUDFRONT_DOMAIN}/{path_quoted}"
    
    # Define expiração para daqui a 2 horas
    expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    
    signer = CloudFrontSigner(settings.CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)
    
    # Gera a URL com os parâmetros de assinatura anexados
    return signer.generate_presigned_url(url, date_less_than=expire_date)

# Sua View de Detalhes do Vídeo Atualizada
class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video_atual = self.object
        
        # --- PROTEÇÃO AQUI ---
        # Geramos a URL assinada para o arquivo do vídeo
        # video_atual.arquivo é o campo FileField/CharField que guarda 'videos/nome.mp4'
        context['url_assinada'] = generate_cloudfront_url(str(video_atual.arquivo))
        
        # Lógica de navegação de aulas que você já tinha
        aula = video_atual.lesson_set.first() 
        if aula:
            modulo = aula.module
            context['proxima_aula'] = modulo.lessons.filter(id__gt=aula.id).order_by('id').first()
            context['aula_anterior'] = modulo.lessons.filter(id__lt=aula.id).order_by('-id').first()
        
        return context

# Upload de Vídeo bruto
class VideoCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'core/video_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all().order_by('title') # Envia os cursos para o seletor
        return context

@login_required
def get_presigned_url(request):
    file_name = request.GET.get('file_name')
    file_type = request.GET.get('file_type')

    if not file_name or not file_type:
        return JsonResponse({'error': 'Nome ou tipo de arquivo ausente'}, status=400)
    
    # --- CORREÇÃO 1: Lógica de Pastas ---
    # Se for imagem, manda para thumbnails. Se não, assume que é video.
    if file_type.startswith('image/'):
        folder = 'course_thumbnails'
    else:
        folder = 'videos'
    
    # Caminho final do arquivo (Key)
    file_key = f"{folder}/{file_name}"
    # ------------------------------------

    try:
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME
        )

        presigned_post = s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"videos/{file_name}",
            Fields={"Content-Type": file_type},
            Conditions=[
                {"Content-Type": file_type},
                ["content-length-range", 0, 524288000]
            ],
            ExpiresIn=3600
        )
        presigned_post['cloudfront_url'] = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"
        
        return JsonResponse(presigned_post)

    except Exception as e:
        # Isso vai imprimir o erro real no log do Gunicorn para você ler
        print(f"ERRO S3: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def confirm_upload(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        titulo = request.POST.get('titulo')
        modulo_id = request.POST.get('modulo_id') # Enviado pelo JS

        # Cria o vídeo
        novo_video = Video.objects.create(
            titulo=titulo,
            arquivo=f"videos/{file_name}" 
        )

        # Se tiver um módulo, já cria a Aula vinculada
        if modulo_id:
            modulo = Module.objects.get(id=modulo_id)
            Lesson.objects.create(
                module=modulo,
                title=titulo,
                video=novo_video
            )
        
        return JsonResponse({'status': 'success'})
    
@login_required
def get_modules(request, course_id):
    modulos = Module.objects.filter(course_id=course_id).values('id', 'title')
    return JsonResponse(list(modulos), safe=False)