from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import log_action
from .forms import PropertyForm, PropertySearchForm
from .models import Property


def _is_registrar(user):
    return user.is_authenticated and hasattr(user, 'profile') and \
           user.profile.role in ('registrar', 'admin')


def property_list(request):
    form = PropertySearchForm(request.GET or None)
    qs = Property.objects.select_related('registered_owner__profile')

    if form.is_valid() and form.cleaned_data.get('query'):
        q = form.cleaned_data['query']
        qs = qs.filter(
            Q(title_deed_number__icontains=q) |
            Q(stand_number__icontains=q) |
            Q(suburb__icontains=q) |
            Q(city__icontains=q)
        )

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'properties/list.html', {
        'form': form, 'page_obj': page_obj,
    })


def property_detail(request, pk):
    property_obj = get_object_or_404(
        Property.objects.select_related('registered_owner__profile'),
        pk=pk,
    )
    return render(request, 'properties/detail.html', {'property': property_obj})


@login_required
def property_add(request):
    if not _is_registrar(request.user):
        return HttpResponseForbidden(
            "Only Registrars and Admins can add properties."
        )
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save()
            log_action(request.user, 'add_property', 'related_property', prop.id,
                       description=f'Added {prop}', request=request)
            messages.success(request, f'Property "{prop}" added to registry.')
            return redirect('properties:detail', pk=prop.pk)
    else:
        form = PropertyForm()
    return render(request, 'properties/form.html', {'form': form, 'mode': 'Add'})


@login_required
def property_edit(request, pk):
    if not _is_registrar(request.user):
        return HttpResponseForbidden(
            "Only Registrars and Admins can edit registry entries."
        )
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()
            log_action(request.user, 'edit_property', 'related_property', prop.id,
                       description=f'Edited {prop}', request=request)
            messages.success(request, 'Property updated.')
            return redirect('properties:detail', pk=prop.pk)
    else:
        form = PropertyForm(instance=prop)
    return render(request, 'properties/form.html', {
        'form': form, 'mode': 'Edit', 'related_property': prop,
    })