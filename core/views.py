from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video, Course, Module, Lesson
import boto3
import os
import datetime
import urllib.parse
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from botocore.signers import CloudFrontSigner

# --- CLOUDFRONT SIGNER HELPER ---
def rsa_signer(message):
    try:
        if not settings.CLOUDFRONT_PRIVATE_KEY:
            print("AVISO: CLOUDFRONT_PRIVATE_KEY não configurada.")
            return None
            
        private_key = serialization.load_pem_private_key(
            settings.CLOUDFRONT_PRIVATE_KEY.encode(),
            password=None
        )
        return private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
    except Exception as e:
        print(f"Erro no RSA Signer: {e}")
        return None

def generate_cloudfront_url(file_path):
    if not file_path:
        return None
    try:
        path_quoted = urllib.parse.quote(str(file_path))
        url = f"https://{settings.CLOUDFRONT_DOMAIN}/{path_quoted}"
        expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        
        if not settings.CLOUDFRONT_PUBLIC_KEY_ID:
             # Se não tiver chave configurada, retorna URL simples (pode falhar se for privado)
            return url

        signer = CloudFrontSigner(settings.CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)
        return signer.generate_presigned_url(url, date_less_than=expire_date)
    except Exception as e:
        print(f"Erro ao gerar URL CloudFront: {e}")
        return f"https://{settings.CLOUDFRONT_DOMAIN}/{file_path}"

# --- VIEWS ---

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    login_url = '/accounts/login/'

    def get_queryset(self):
        return Course.objects.filter(is_published=True).order_by('-created_at')

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('search_lesson')
        if query:
            context['search_results'] = Lesson.objects.filter(
                module__course=self.object, 
                title__icontains=query
            )
            context['is_searching'] = True
        return context

class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video_atual = self.object
        context['url_assinada'] = generate_cloudfront_url(video_atual.arquivo)
        
        aula = video_atual.lesson_set.first() 
        if aula:
            modulo = aula.module
            context['proxima_aula'] = modulo.lessons.filter(id__gt=aula.id).order_by('id').first()
            context['aula_anterior'] = modulo.lessons.filter(id__lt=aula.id).order_by('-id').first()
        return context

class VideoCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'core/video_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all().order_by('title')
        return context

# --- API ENDPOINTS (AQUI ESTAVA O PROBLEMA) ---

@login_required
def get_presigned_url(request):
    """
    Gera URL assinada para upload direto no S3.
    Diferencia automaticamente entre 'videos' e 'course_thumbnails'.
    """
    file_name = request.GET.get('file_name', '')
    file_type = request.GET.get('file_type', '')

    print(f"DEBUG S3: Solicitacao de Upload - Arquivo: {file_name} | Tipo: {file_type}", flush=True)

    if not file_name:
        return JsonResponse({'error': 'Nome do arquivo obrigatorio'}, status=400)

    # 1. Determina a pasta correta
    f_lower = file_name.lower()
    t_lower = file_type.lower()
    
    # Se for imagem (por tipo ou extensão), vai para thumbnails
    if 'image' in t_lower or f_lower.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        folder = 'course_thumbnails'
        print(f"DEBUG S3: -> Detectado como IMAGEM. Pasta: {folder}", flush=True)
    else:
        folder = 'videos'
        print(f"DEBUG S3: -> Detectado como VIDEO. Pasta: {folder}", flush=True)

    file_key = f"{folder}/{file_name}"

    try:
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME
        )

        presigned_post = s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_key,
            Fields={"Content-Type": file_type or 'application/octet-stream'},
            Conditions=[
                # Removemos content-type estrito para evitar erros de validação do browser
                ["content-length-range", 0, 524288000], # Até 500MB
            ],
            ExpiresIn=3600
        )
        
        # IMPORTANTE: Retorna a URL pública do CloudFront para o Javascript usar no preview
        presigned_post['cloudfront_url'] = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"

        return JsonResponse(presigned_post)

    except Exception as e:
        print(f"ERRO CRÍTICO NO S3: {str(e)}", flush=True)
        return JsonResponse({'error': f"Erro no servidor: {str(e)}"}, status=500)

@login_required
def confirm_upload(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        titulo = request.POST.get('titulo')
        modulo_id = request.POST.get('modulo_id')
        
        # O arquivo já está no S3, apenas salvamos a referência
        # Nota: Ajuste a pasta se necessário, aqui assume videos/
        # Se for imagem, você não usa essa view, o widget salva direto.
        novo_video = Video.objects.create(
            titulo=titulo,
            arquivo=f"videos/{file_name}" 
        )

        if modulo_id:
            try:
                modulo = Module.objects.get(id=modulo_id)
                Lesson.objects.create(module=modulo, title=titulo, video=novo_video)
            except Module.DoesNotExist:
                pass
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Metodo nao permitido'}, status=405)

@login_required
def get_modules(request, course_id):
    modulos = Module.objects.filter(course_id=course_id).values('id', 'title')
    return JsonResponse(list(modulos), safe=False)