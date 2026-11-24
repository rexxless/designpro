from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm, RequestCreateForm
from .models import Status


def index(request):
    return render(request, 'index.html')


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

@login_required
def request_create(request):
    if request.method == 'POST':
        form = RequestCreateForm(request.POST, request.FILES)
        if form.is_valid():
            created_request = form.save(commit=False)
            created_request.user = request.user.profile
            created_request.status = Status.objects.get(code=Status.Code.NEW)
            created_request.save()
            messages.success(request, f'Заявка сохранена. Ваш номер заявки: {created_request.pk}')
            return redirect('index')

    else:
        form = RequestCreateForm()

    return render(request, 'requests/create.html', {'form': form})

def request_detail(request, pk):
    return 
