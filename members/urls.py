from django.urls import path
from . import views

urlpatterns = [
 path('', views.home, name='home'),
 path('register/', views.register_user, name='register'),
 path('login/', views.login_user, name='login'),
 path('logout/',views.logout_user, name='logout'),
 path('send_message/', views.send_message, name='send_message'),
 path('api/get_messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
 path('api/get_conversations/', views.get_conversations, name='get_conversations'),
]