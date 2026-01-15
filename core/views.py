from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Video, Course, Module, Lesson
import boto3
import os
import datetime
import urllib.parse
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.text import get_valid_filename # <--- IMPORTANTE
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from botocore.signers import CloudFrontSigner

# --- CLOUDFRONT SIGNER HELPER ---
def rsa_signer(message):
    try:
        if not settings.CLOUDFRONT_PRIVATE_KEY:
            return None
        private_key = serialization.load_pem_private_key(
            settings.CLOUDFRONT_PRIVATE_KEY.encode(),
            password=None
        )
        return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())
    except Exception as e:
        print(f"Erro RSA Signer: {e}")
        return None

def generate_cloudfront_url(file_path):
    if not file_path: return None
    try:
        path_quoted = urllib.parse.quote(str(file_path))
        url = f"https://{settings.CLOUDFRONT_DOMAIN}/{path_quoted}"
        if not settings.CLOUDFRONT_PUBLIC_KEY_ID: return url
        
        expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        signer = CloudFrontSigner(settings.CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)
        return signer.generate_presigned_url(url, date_less_than=expire_date)
    except Exception as e:
        print(f"Erro URL CloudFront: {e}")
        return f"https://{settings.CLOUDFRONT_DOMAIN}/{file_path}"

# --- VIEWS ---
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    login_url = '/accounts/login/'
    def get_queryset(self): return Course.objects.filter(is_published=True).order_by('-created_at')

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'
    context_object_name = 'course'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('search_lesson'):
            context['search_results'] = Lesson.objects.filter(module__course=self.object, title__icontains=self.request.GET.get('search_lesson'))
            context['is_searching'] = True
        return context

class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_assinada'] = generate_cloudfront_url(self.object.arquivo)
        aula = self.object.lesson_set.first() 
        if aula:
            context['proxima_aula'] = aula.module.lessons.filter(id__gt=aula.id).order_by('id').first()
            context['aula_anterior'] = aula.module.lessons.filter(id__lt=aula.id).order_by('-id').first()
        return context

class VideoCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'core/video_form.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all().order_by('title')
        return context

# --- API ENDPOINTS CORRIGIDOS ---

@login_required
def get_presigned_url(request):
    raw_file_name = request.GET.get('file_name', '')
    file_type = request.GET.get('file_type', '')

    print(f"DEBUG S3: Solicitacao Upload - '{raw_file_name}' ({file_type})", flush=True)

    if not raw_file_name:
        return JsonResponse({'error': 'Nome do arquivo ausente'}, status=400)

    # 1. Sanitização do Nome (Remove espaços e acentos que causam erro 403)
    # Ex: "Minha Foto.jpg" vira "Minha_Foto.jpg"
    safe_name = get_valid_filename(raw_file_name)
    
    # 2. Lógica de Pastas
    folder = 'videos'
    if 'image' in file_type.lower() or safe_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        folder = 'course_thumbnails'
        print(f"DEBUG S3: -> Definido como IMAGEM. Pasta: {folder}", flush=True)
    
    file_key = f"{folder}/{safe_name}"

    try:
        s3_client = boto3.client('s3', region_name=settings.AWS_S3_REGION_NAME)
        
        presigned_post = s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_key,
            Fields={"Content-Type": file_type},
            Conditions=[
                {"Content-Type": file_type}, # Restauramos a validação estrita que funcionava
                ["content-length-range", 0, 524288000]
            ],
            ExpiresIn=3600
        )
        
        # URL Pública do CloudFront para o Widget salvar no banco
        presigned_post['cloudfront_url'] = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"

        return JsonResponse(presigned_post)
    except Exception as e:
        print(f"ERRO S3: {e}", flush=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def confirm_upload(request):
    if request.method == 'POST':
        # Nota: Essa view é usada apenas pelo upload de Vídeos, não de imagens
        file_name = request.POST.get('file_name') # Aqui o JS manda o nome original, cuidado
        titulo = request.POST.get('titulo')
        modulo_id = request.POST.get('modulo_id')
        
        # Importante: O JS do vídeo também deve usar o nome sanitizado se possível, 
        # mas aqui vamos apenas salvar o caminho.
        # Se você usar o widget de imagem, ele já salva a URL completa direto no Admin.
        
        path = f"videos/{file_name}" # Mantenha simples para vídeos por enquanto
        novo_video = Video.objects.create(titulo=titulo, arquivo=path)
        
        if modulo_id:
            try:
                Lesson.objects.create(module_id=modulo_id, title=titulo, video=novo_video)
            except: pass
            
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Metodo invalido'}, status=405)

@login_required
def get_modules(request, course_id):
    return JsonResponse(list(Module.objects.filter(course_id=course_id).values('id', 'title')), safe=False)