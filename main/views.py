from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm, RequestCreateForm, RequestUpdateForm
from .models import Profile, Request, Status


def request_for_user(user):
    if user.is_superuser:
        return Request.objects.all()
    return Request.objects.filter(user=user)


def index(request):
    return render(request, 'index.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Profile.objects.create(
                    user=user,
                    patronymic=form.cleaned_data['patronymic'],
                )
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
            created_request.user = request.user
            created_request.status = Status.objects.get(code=Status.Code.NEW)
            created_request.save()
            messages.success(request, f'Заявка сохранена. Ваш номер заявки: {created_request.pk}')
            return redirect('index')

    else:
        form = RequestCreateForm()

    return render(request, 'requests/create.html', {'form': form})

@login_required
def request_detail(request, pk):
    design_request = get_object_or_404(request_for_user(request.user), pk=pk)
    return render(request, 'requests/detail.html', {'design_request': design_request})


@login_required
def request_list(request):
    design_requests = request_for_user(request.user).select_related('category', 'status')
    status_options = list(Status.objects.all())
    requested_status = request.GET.get('status')
    selected_status = next(
        (status.pk for status in status_options if str(status.pk) == requested_status),
        None,
    )
    if selected_status is not None:
        design_requests = design_requests.filter(status_id=selected_status)

    return render(request, 'requests/list.html', {
        'design_requests': design_requests,
        'status_options': status_options,
        'selected_status': selected_status,
    })


@login_required
def request_update(request, pk):
    design_request = get_object_or_404(request_for_user(request.user), pk=pk)
    if request.method == 'POST':
        form = RequestUpdateForm(request.POST, request.FILES, instance=design_request)
        if form.is_valid():
            if form.has_changed():
                updated_request = form.save(commit=False)
                updated_request.save(update_fields=[*form.changed_data, 'updated_at'])
                messages.success(request, 'Изменения сохранены.')
            return redirect(design_request)
    else:
        form = RequestUpdateForm(instance=design_request)

    return render(request, 'requests/update.html', {
        'form': form,
        'design_request': design_request,
    })


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def request_delete(request, pk):
    deletable_requests = request_for_user(request.user)
    if not request.user.is_superuser:
        deletable_requests = deletable_requests.filter(status__code=Status.Code.NEW)

    if request.method == 'POST':
        with transaction.atomic():
            design_request = get_object_or_404(deletable_requests.select_for_update(), pk=pk)
            design_request.delete()
        messages.success(request, 'Заявка удалена.')
        return redirect('request-list')

    design_request = get_object_or_404(deletable_requests, pk=pk)
    return render(request, 'requests/confirm_delete.html', {'design_request': design_request})
