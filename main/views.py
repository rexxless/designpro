from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from .forms import (
    CategoryForm,
    RegistrationForm,
    RequestCreateForm,
    RequestStatusForm,
    RequestUpdateForm,
)
from .models import Category, Profile, Request, Status


def request_for_user(user):
    if user.is_superuser:
        return Request.objects.all()
    return Request.objects.filter(user=user)


def published_designs():
    return Request.objects.filter(
        status__code=Status.Code.COMPLETED,
        final_image__isnull=False,
    ).exclude(final_image='')


def index(request):
    completed_requests = published_designs().select_related('category').order_by('-created_at', '-pk')[:4]
    in_progress_count = Request.objects.filter(status__code=Status.Code.IN_PROGRESS).count()
    return render(request, 'index.html', {
        'completed_requests': completed_requests,
        'in_progress_count': in_progress_count,
    })


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


def serve_request_image(image):
    if not image:
        raise Http404
    try:
        response = FileResponse(image.open('rb'))
    except FileNotFoundError as error:
        raise Http404 from error
    response.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


@login_required
@never_cache
@require_safe
def request_plan(request, pk):
    design_request = get_object_or_404(request_for_user(request.user), pk=pk)
    return serve_request_image(design_request.plan_image)


@require_safe
def request_design(request, pk):
    design_request = get_object_or_404(published_designs(), pk=pk)
    return serve_request_image(design_request.final_image)


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


def check_studio_access(user):
    if user.is_authenticated and not user.is_superuser:
        raise PermissionDenied
    return user.is_superuser


@user_passes_test(check_studio_access)
@require_http_methods(['GET', 'HEAD'])
def studio_dashboard(request):
    design_requests = Request.objects.select_related('category', 'status')
    return render(request, 'studio/dashboard.html', {'design_requests': design_requests})


@user_passes_test(check_studio_access)
@require_http_methods(['GET', 'HEAD', 'POST'])
def studio_request_status(request, pk):
    pending_requests = Request.objects.filter(status__code=Status.Code.NEW)
    if request.method == 'POST':
        form = RequestStatusForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                design_request = get_object_or_404(pending_requests.select_for_update(), pk=pk)
                design_request.status = form.cleaned_data['status']
                changed_fields = ['status', 'updated_at']
                if design_request.status.code == Status.Code.IN_PROGRESS:
                    design_request.comment = form.cleaned_data['comment']
                    changed_fields.append('comment')
                else:
                    design_request.final_image = form.cleaned_data['final_image']
                    changed_fields.append('final_image')
                design_request.save(update_fields=changed_fields)
            messages.success(request, 'Статус заявки обновлён.')
            return redirect('studio-dashboard')
    else:
        form = RequestStatusForm()

    design_request = get_object_or_404(pending_requests, pk=pk)
    return render(request, 'studio/request_status.html', {
        'form': form,
        'design_request': design_request,
    })


@user_passes_test(check_studio_access)
@require_http_methods(['GET', 'HEAD', 'POST'])
def studio_categories(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория добавлена.')
            return redirect('studio-category-list')
    else:
        form = CategoryForm()

    return render(request, 'studio/categories.html', {
        'form': form,
        'categories': Category.objects.all(),
    })


@user_passes_test(check_studio_access)
@require_http_methods(['GET', 'HEAD', 'POST'])
def studio_category_delete(request, pk):
    if request.method == 'POST':
        with transaction.atomic():
            category = get_object_or_404(Category.objects.select_for_update(), pk=pk)
            category.delete()
        messages.success(request, 'Категория удалена.')
        return redirect('studio-category-list')

    category = get_object_or_404(Category, pk=pk)
    return render(request, 'studio/confirm_category_delete.html', {
        'category': category,
        'affected_count': category.request_set.count(),
    })
