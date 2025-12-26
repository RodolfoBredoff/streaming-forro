from django.urls import path
from .views import CourseListView, CourseDetailView
from .views import CourseListView, CourseDetailView, VideoDetailView
urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('curso/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('aula/<int:pk>/', VideoDetailView.as_view(), name='video_detail'),
] 