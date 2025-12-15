import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .forms import ProfileForm, CustomPasswordChangeForm
from .models import Users

logger = logging.getLogger(__name__)  # Logger for debugging

@login_required
def profilePage(request):
    user = request.user

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=user)
        password_form = CustomPasswordChangeForm(user, request.POST)

        # Log the incoming POST data to check what's being sent
        logger.debug(f"POST data: {request.POST}")

        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, f"Profile updated successfully.")
            return redirect('profilePage')

        elif 'change_password' in request.POST:
            # Log form validity
            logger.debug(f"Password form is valid: {password_form.is_valid()}")

            if password_form.is_valid():
                # Log cleaned data (password values)
                logger.debug(f"Cleaned password data: {password_form.cleaned_data}")

                current_password = password_form.cleaned_data.get('old_password')
                new_password     = password_form.cleaned_data.get('new_password1')
                if new_password != password_form.cleaned_data.get('new_password2'):
                    return JsonResponse({'error': 'New password and confirmation do not match.'}, status=400)



                # If everything is valid, save the new password
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                return JsonResponse({'success': 'Password updated successfully.'}, status=200)

            else:
                # Log form errors if not valid
                logger.debug(f"Password form errors: {password_form.errors}")
                return JsonResponse({'error': password_form.errors.as_text()}, status=400)

        else:
            logger.debug("Form submission failed, no valid form data.")
            return JsonResponse({'error': 'There was an error with the form. Please check the fields and try again.'}, status=400)

    else:
        profile_form = ProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)

    return render(request, 'profile-page.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })
