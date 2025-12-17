from django.db import models

class Video(models.Model):
    titulo = models.CharField(max_length=100)
    arquivo = models.FileField(upload_to='videos/') # Upload vai para o S3
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo