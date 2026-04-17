import json
import boto3
import os
import datetime
import urllib.parse

from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from botocore.signers import CloudFrontSigner

from .models import Video, Course, Module, Lesson, WatchProgress, Favorite


# --- CLOUDFRONT SIGNER HELPER ---

def rsa_signer(message):
    try:
        key_content = settings.CLOUDFRONT_PRIVATE_KEY
        if not key_content:
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
    if not file_path:
        return None
    try:
        path_quoted = urllib.parse.quote(str(file_path))
        url = f"https://{settings.CLOUDFRONT_DOMAIN}/{path_quoted}"
        if not settings.CLOUDFRONT_PUBLIC_KEY_ID:
            return url
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

    def get_queryset(self):
        return Course.objects.filter(is_published=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # "Continue Assistindo": cursos onde o usuário tem progresso mas não completou tudo
        user = self.request.user
        in_progress_video_ids = WatchProgress.objects.filter(
            user=user, completed=False, position_seconds__gt=0
        ).values_list('video_id', flat=True)

        continue_lessons = Lesson.objects.filter(
            video__id__in=in_progress_video_ids
        ).select_related('module__course', 'video').order_by('-video__watch_progresses__updated_at')

        seen_courses = set()
        continue_watching = []
        for lesson in continue_lessons:
            course = lesson.module.course
            if course.id not in seen_courses and course.is_published:
                seen_courses.add(course.id)
                progress = WatchProgress.objects.filter(user=user, video=lesson.video).first()
                continue_watching.append({
                    'course': course,
                    'lesson': lesson,
                    'progress': progress,
                })

        context['continue_watching'] = continue_watching
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if self.request.GET.get('search_lesson'):
            context['search_results'] = Lesson.objects.filter(
                module__course=self.object,
                title__icontains=self.request.GET.get('search_lesson')
            ).select_related('video')
            context['is_searching'] = True

        # Build a map of video_id -> WatchProgress for all lessons in this course
        all_lessons = Lesson.objects.filter(module__course=self.object).select_related('video')
        video_ids = [l.video_id for l in all_lessons if l.video_id]
        progresses = WatchProgress.objects.filter(user=user, video_id__in=video_ids)
        progress_map = {p.video_id: p for p in progresses}
        context['progress_map'] = progress_map

        # Favorites set for this course
        fav_lesson_ids = set(
            Favorite.objects.filter(user=user, lesson__module__course=self.object).values_list('lesson_id', flat=True)
        )
        context['fav_lesson_ids'] = fav_lesson_ids

        return context


class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'core/video_detail.html'
    context_object_name = 'video'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_assinada'] = generate_cloudfront_url(self.object.arquivo)

        aula = self.object.lesson_set.select_related('module__course').first()
        if aula:
            # Use order field for proper prev/next, fall back to id
            context['proxima_aula'] = (
                aula.module.lessons.filter(order__gt=aula.order).order_by('order').first()
                or aula.module.lessons.filter(id__gt=aula.id).order_by('id').first()
            )
            context['aula_anterior'] = (
                aula.module.lessons.filter(order__lt=aula.order).order_by('-order').first()
                or aula.module.lessons.filter(id__lt=aula.id).order_by('-id').first()
            )
            context['aula_atual'] = aula
            context['curso'] = aula.module.course
            context['modulo'] = aula.module
            # All lessons in the same module for sidebar
            context['modulo_aulas'] = aula.module.lessons.select_related('video').all()

        # Watch progress (resume)
        watch_progress = WatchProgress.objects.filter(
            user=self.request.user, video=self.object
        ).first()
        context['watch_progress'] = watch_progress

        # Favorite status
        if aula:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, lesson=aula
            ).exists()
        else:
            context['is_favorite'] = False

        return context


class VideoCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'core/video_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all().order_by('title')
        return context


class FavoritesView(LoginRequiredMixin, ListView):
    template_name = 'core/favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('lesson__module__course', 'lesson__video').order_by('-created_at')


# --- API ENDPOINTS ---

@login_required
@require_POST
def save_progress(request):
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        position = float(data.get('position_seconds', 0))
        duration = float(data.get('duration', 0))

        if not video_id:
            return JsonResponse({'error': 'video_id ausente'}, status=400)

        video = Video.objects.get(pk=video_id)
        completed = duration > 0 and (position / duration) >= 0.9

        progress, _ = WatchProgress.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={'position_seconds': position, 'completed': completed},
        )
        return JsonResponse({'status': 'ok', 'completed': progress.completed})
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Vídeo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_favorite(request):
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')

        if not lesson_id:
            return JsonResponse({'error': 'lesson_id ausente'}, status=400)

        lesson = Lesson.objects.get(pk=lesson_id)
        fav, created = Favorite.objects.get_or_create(user=request.user, lesson=lesson)
        if not created:
            fav.delete()
            return JsonResponse({'is_favorite': False})
        return JsonResponse({'is_favorite': True})
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'Aula não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_presigned_url(request):
    raw_file_name = request.GET.get('file_name', '')
    file_type = request.GET.get('file_type', '')

    print(f"DEBUG S3: Solicitacao Upload - '{raw_file_name}' ({file_type})", flush=True)

    if not raw_file_name:
        return JsonResponse({'error': 'Nome do arquivo ausente'}, status=400)

    safe_name = get_valid_filename(raw_file_name)

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
                {"Content-Type": file_type},
                ["content-length-range", 0, 524288000]
            ],
            ExpiresIn=3600
        )
        presigned_post['cloudfront_url'] = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"
        return JsonResponse(presigned_post)
    except Exception as e:
        print(f"ERRO S3: {e}", flush=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def confirm_upload(request):
    if request.method == 'POST':
        raw_file_name = request.POST.get('file_name')
        titulo = request.POST.get('titulo')
        modulo_id = request.POST.get('modulo_id')

        safe_name = get_valid_filename(raw_file_name)
        path = f"videos/{safe_name}"
        novo_video = Video.objects.create(titulo=titulo, arquivo=path)

        if modulo_id:
            try:
                modulo = Module.objects.get(id=modulo_id)
                Lesson.objects.create(module=modulo, title=titulo, video=novo_video)
            except Module.DoesNotExist:
                pass

        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Metodo invalido'}, status=405)


@login_required
def get_modules(request, course_id):
    return JsonResponse(
        list(Module.objects.filter(course_id=course_id).values('id', 'title')),
        safe=False
    )
