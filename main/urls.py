from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/register/', views.register, name='register'),
    path('request/create/', views.request_create, name='request-create'),

]
