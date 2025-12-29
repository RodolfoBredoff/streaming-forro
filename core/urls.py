from django.urls import path
from .views import CourseListView, CourseDetailView
from .views import CourseListView, CourseDetailView, VideoDetailView
from . import views

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('curso/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('aula/<int:pk>/', VideoDetailView.as_view(), name='video_detail'),
    # Rota que renderiza o formulário de upload
    path('upload/', views.VideoCreateView.as_view(), name='video_upload'),
    # Rotas da API para o Direct Upload ao S3
    path('api/get-presigned-url/', views.get_presigned_url, name='get_presigned_url'),
    path('api/confirm-upload/', views.confirm_upload, name='confirm_upload'),
] 