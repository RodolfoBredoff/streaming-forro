from django.urls import path
from .views import CourseListView, VideoDetailView # e outras que usar

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    # path('video/<int:pk>/', VideoDetailView.as_view(), name='video_detail'),
]