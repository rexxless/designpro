from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/register/', views.register, name='register'),
    path('request/', views.request_list, name='request-list'),
    path('request/create/', views.request_create, name='request-create'),
    path('request/<int:pk>/', views.request_detail, name='request-detail'),
    path('request/<int:pk>/plan/', views.request_plan, name='request-plan'),
    path('gallery/<int:pk>/image/', views.request_design, name='request-design'),
    path('request/<int:pk>/update/', views.request_update, name='request-update'),
    path('request/<int:pk>/delete/', views.request_delete, name='request-delete'),
    path('superadmin/', views.studio_dashboard, name='studio-dashboard'),
    path('superadmin/requests/<int:pk>/status/', views.studio_request_status, name='studio-request-status'),
    path('superadmin/categories/', views.studio_categories, name='studio-category-list'),
    path('superadmin/categories/<int:pk>/delete/', views.studio_category_delete, name='studio-category-delete'),
]
