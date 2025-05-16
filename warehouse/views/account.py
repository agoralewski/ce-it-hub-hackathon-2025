"""
User account and authentication views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from warehouse.forms import CustomUserCreationForm, UserProfileForm


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'warehouse/profile.html')


@login_required
def edit_profile(request):
    """Edit user profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been successfully updated!'))
            return redirect('warehouse:profile')
        else:
            messages.error(request, _('Please correct the errors in the form.'))
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'warehouse/edit_profile.html', {'form': form})


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
            messages.success(request, _('Your password has been successfully changed!'))
            return redirect('warehouse:profile')
        else:
            messages.error(request, _('Please correct the errors in the form.'))
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'warehouse/change_password.html', {'form': form})


def custom_logout(request):
    """Custom logout view to ensure proper redirection"""
    logout(request)
    messages.success(request, _('You have been successfully logged out.'))
    return redirect('login')


def register(request):
    """Registration view for new users"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Account has been successfully created! You can now log in.'),
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})