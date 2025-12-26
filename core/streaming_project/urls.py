from django.urls import path
from .views import CourseListView # Aqui a importação funciona pois a view está na mesma pasta

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
]