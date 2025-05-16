"""
User account and authentication views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

from warehouse.forms import CustomUserCreationForm


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'warehouse/profile.html')


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(
                request, user
            )  # Important to keep the user logged in
            messages.success(request, 'Twoje hasło zostało pomyślnie zmienione!')
            return redirect('warehouse:profile')
        else:
            messages.error(request, 'Proszę poprawić błędy w formularzu.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'warehouse/change_password.html', {'form': form})


def custom_logout(request):
    """Custom logout view to ensure proper redirection"""
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('login')


def register(request):
    """Registration view for new users"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Konto zostało pomyślnie utworzone! Możesz się teraz zalogować.',
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})