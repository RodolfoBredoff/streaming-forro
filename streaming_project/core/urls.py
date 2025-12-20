from django.urls import path
from .views import VideoListView, VideoDetailView, VideoCreateView

urlpatterns = [
    path('', VideoListView.as_view(), name='video-list'),
    path('assistir/<int:pk>/', VideoDetailView.as_view(), name='video-detail'),
    path('upload/', VideoCreateView.as_view(), name='video-upload'),
]