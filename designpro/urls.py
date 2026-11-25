"""URL configuration for designpro project."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from main.views import PortalLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),

    path('accounts/login/', PortalLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/',
         auth_views.PasswordChangeView.as_view(template_name='registration/portal_password_change.html'),
         name='password_change'),
    path('accounts/password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/portal_password_change.html'),
         name='password_change_done'),
]
