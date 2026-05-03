from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import SignUpForm, EmailLoginForm, ProfileUpdateForm
from .models import log_action


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(
                request, user,
                backend='accounts.backends.EmailBackend',
            )
            log_action(user, 'signup', 'User', user.id,
                       description=f'New {user.profile.role} signed up',
                       request=request)
            messages.success(request, f'Welcome to LandGuard, {user.profile.full_name}!')
            return redirect('dashboard:home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                log_action(user, 'login', 'User', user.id, request=request)
                messages.success(request, f'Welcome back, {user.profile.full_name}.')
                next_url = request.GET.get('next') or 'dashboard:home'
                return redirect(next_url)
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    log_action(request.user, 'logout', 'User', request.user.id, request=request)
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_action(request.user, 'update_profile', 'Profile', profile.id,
                       request=request)
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'accounts/profile.html', {
        'form': form, 'profile': profile,
    })
