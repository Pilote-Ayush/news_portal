from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .forms import RegisterForm, ProfileForm, EmailChangeForm
from .models import User
from news.models import News, Follow

# Password change view using Django's built-in class-based view
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile', kwargs={'username': None})  # Will override in get_success_url

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})


# Email change view
@login_required
def change_email(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email updated successfully!')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = EmailChangeForm(instance=request.user)
    return render(request, 'accounts/change_email.html', {'form': form})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileForm
from .models import User
from news.models import News

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'journalist':
                return redirect('journalist_dashboard')
            elif user.role == 'advertiser':
                return redirect('advertiser_dashboard')
            else:
                return redirect('home')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    user_news = News.objects.filter(author=user_obj, is_approved=True).order_by('-created_at')

    is_following = False
    can_view = True
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=user_obj).exists()
        # If profile is private and user is not the owner and not following, restrict access
        if user_obj.is_private and request.user != user_obj and not is_following:
            can_view = False
            user_news = News.objects.none()  # Don't show any news

    followers_count = user_obj.followers.count() if hasattr(user_obj, 'followers') else 0
    following_count = user_obj.following.count() if hasattr(user_obj, 'following') else 0

    return render(request, 'accounts/profile.html', {
        'profile_user': user_obj,
        'user_news': user_news,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'can_view': can_view,
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if request.user != user_to_follow:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    return redirect('accounts:profile', username=username)


@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    return redirect('accounts:profile', username=username)