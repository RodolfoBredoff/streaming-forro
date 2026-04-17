from django.urls import path
from . import views # Isso já importa CourseListView, VideoCreateView, etc.

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('curso/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('aula/<int:pk>/', views.VideoDetailView.as_view(), name='video_detail'),
    
    # Rota de upload
    path('upload/', views.VideoCreateView.as_view(), name='video_upload'),
    
    # Favoritos
    path('favoritos/', views.FavoritesView.as_view(), name='favorites'),

    # APIs
    path('api/get-presigned-url/', views.get_presigned_url, name='get_presigned_url'),
    path('api/confirm-upload/', views.confirm_upload, name='confirm_upload'),
    path('api/get-modules/<int:course_id>/', views.get_modules, name='get_modules'),
    path('api/save-progress/', views.save_progress, name='save_progress'),
    path('api/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
]