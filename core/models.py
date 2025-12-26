from django.db import models
from django.utils.text import slugify

class Video(models.Model):
    titulo = models.CharField(max_length=100)
    arquivo = models.FileField(upload_to='videos/') # Upload vai para o S3
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

# --- NOVOS MODELOS PARA A PLATAFORMA PROFISSIONAL ---

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título do Curso")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(verbose_name="Descrição")
    thumbnail = models.ImageField(upload_to='course_thumbnails/', verbose_name="Capa do Curso")
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False, verbose_name="Publicado")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="Nome do Módulo")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="Título da Aula")
    content = models.TextField(blank=True, verbose_name="Material de Apoio (Texto)")
    # Aqui fazemos o vínculo com o seu modelo original de Video
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    free_preview = models.BooleanField(default=False, verbose_name="Aula Grátis")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title