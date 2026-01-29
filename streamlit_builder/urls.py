from django.contrib import admin
from django.urls import path
from builder import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('download/', views.download_bundle, name='download_bundle'),
]
