from django.urls import path
from .views import CourseListView, VideoDetailView # e outras que usar

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('curso/<int:pk>/', CourseDetailView.as_view(), name='course_detail'), # Mudamos para int:pk