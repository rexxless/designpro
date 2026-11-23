"""URL configuration for designpro project."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from main.forms import LoginForm, StyledPasswordResetForm, StyledSetPasswordForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),

    # Auth views with Bootstrap-styled forms; these must come before the
    # django.contrib.auth.urls include so they take precedence.
    path('accounts/login/',
         auth_views.LoginView.as_view(authentication_form=LoginForm, redirect_authenticated_user=True),
         name='login'),
    path('accounts/password_reset/',
         auth_views.PasswordResetView.as_view(form_class=StyledPasswordResetForm),
         name='password_reset'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(form_class=StyledSetPasswordForm),
         name='password_reset_confirm'),
    path('accounts/', include('django.contrib.auth.urls')),
]
