import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from axes.handlers.proxy import AxesProxyHandler

from .forms import RegistrationForm, KYCAuthenticationForm
from .models import CustomUser

security_logger = logging.getLogger('accounts.security')


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            security_logger.info(f"New user registered: {user.username} from IP {get_client_ip(request)}")
            messages.success(request, f'Welcome, {user.first_name or user.username}! Your account has been created.')
            return redirect('dashboard')
        else:
            security_logger.warning(f"Failed registration attempt from IP {get_client_ip(request)}")
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = KYCAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            security_logger.info(f"Successful login: {user.username} from IP {get_client_ip(request)}")
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            security_logger.warning(
                f"Failed login attempt for '{request.POST.get('username', 'unknown')}' "
                f"from IP {get_client_ip(request)}"
            )
    else:
        form = KYCAuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    security_logger.info(f"User {request.user.username} logged out from IP {get_client_ip(request)}")
    logout(request)
    messages.info(request, 'You have been securely logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


def lockout_view(request, *args, **kwargs):
    security_logger.warning(f"Account locked out from IP {get_client_ip(request)}")
    return render(request, 'registration/lockout.html', status=403)
