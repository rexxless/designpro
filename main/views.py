from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def index(request):
    return render(request, 'base_generic.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Добро пожаловать в Design.pro, {user.username}!')
            return redirect('index')
    else:
        form = RegistrationForm()

    return render(request, 'registration/registration.html', {'form': form})
