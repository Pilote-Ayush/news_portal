from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .forms import NewsForm, CommentForm
from .models import News, Comment, Bookmark, Notification, Tag, Follow
from django.db.models import Q
from django.core.mail import send_mail
from news.models import Follow, News
from django.core.paginator import Paginator

User = get_user_model()
admin_user = User.objects.first()


def home(request):
    
    
    save_news()  # Fetch and save news from API on home page load
    return HttpResponse(News.objects.count())
    category = request.GET.get('category')
    search_query = request.GET.get('search')

    news_list = News.objects.all().order_by('-created_at')

    # CATEGORY FILTER
    if category and category != "All":
        news_list = news_list.filter(category__name__iexact=category)

    # SEARCH FILTER
    if search_query:
        news_list = news_list.filter(title__icontains=search_query)

    # ✅ PAGINATION ADD
    paginator = Paginator(news_list, 2)  # 2 news per page
    page_number = request.GET.get('page')
    news = paginator.get_page(page_number)

    # BREAKING
    breaking_news = News.objects.filter(breaking=True)

    # TRENDING
    trending_news = News.objects.filter(is_trending=True)

    context = {
        'news': news,  # 👈 IMPORTANT (page_obj j che aa)
        'breaking_news': breaking_news,
        'trending_news': trending_news
    }

    return render(request, 'news/home.html', context)

@login_required
def create_news(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.is_approved = False
            news.save()

            # Handle tags
            tags_str = form.cleaned_data.get('tags')
            if tags_str:
                tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    news.tags.add(tag)

            Notification.objects.create(
                user=request.user,
                news=news,
                message=f"Your news '{news.title}' has been submitted and is pending approval."
            )

            for admin in User.objects.filter(is_superuser=True):
                Notification.objects.create(
                    user=admin,
                    news=news,
                    message=f"New news '{news.title}' submitted by {request.user.username}."
                )

            return redirect('news:news_detail', id=news.id)

    else:
        form = NewsForm()

    return render(request, 'news/create_news.html', {'form': form})


@login_required
def approve_news(request, id):
    news = get_object_or_404(News, id=id)

    if not request.user.is_superuser:
        return redirect('home')

    news.is_approved = True
    news.save()

    Notification.objects.create(
        user=news.author,
        news=news,
        message=f"Your news '{news.title}' has been approved by admin."
    )

    return redirect('news:news_detail', id=id)


def news_detail(request, id):
    news = get_object_or_404(News, id=id,)

    news.views += 1
    news.save()

    # Get related articles based on shared tags
    related_articles = News.objects.filter(
        tags__in=news.tags.all(),
        is_approved=True
    ).exclude(id=news.id).distinct()[:5]  # Limit to 5 related articles

    return render(request, 'news/news_detail.html', {
        'news': news,
        'related_articles': related_articles
    })


@login_required
def edit_news(request, id):

    news = get_object_or_404(News, id=id)

    # Only author or admin edit kari shake
    if request.user != news.author and not request.user.is_superuser:
        return redirect("home")

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save()

            # Handle tags
            news.tags.clear()  # Clear existing tags
            tags_str = form.cleaned_data.get('tags')
            if tags_str:
                tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    news.tags.add(tag)

            return redirect('news:news_detail', id=news.id)
    else:
        form = NewsForm(instance=news)

    return render(request, 'news/edit_news.html', {'form': form})


@login_required
def delete_news(request, id):
    news = get_object_or_404(News, id=id)

    if request.user == news.author or request.user.is_superuser:
        news.delete()

    return redirect("home")


@login_required
def like_news(request, id):
    news = get_object_or_404(News, id=id)

    if request.user in news.likes.all():
        news.likes.remove(request.user)
        Notification.objects.create(
            user=request.user,
            news=news,
            message=f"You unliked '{news.title}'."
        )
    else:
        news.likes.add(request.user)
        Notification.objects.create(
            user=request.user,
            news=news,
            message=f"You liked '{news.title}'."
        )

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def add_comment(request, id):

    news = News.objects.get(id=id)

    if request.method == "POST":
        text = request.POST.get("text")

        comment = Comment.objects.create(
            news=news,
            user=request.user,
            text=text
        )

        # Send email notification to author if not the commenter
        if news.author != request.user and news.author.email:
            send_mail(
                subject=f'New comment on your article: {news.title}',
                message=f'Hi {news.author.username},\n\n{request.user.username} commented on your article "{news.title}":\n\n"{text}"\n\nView the article: {request.build_absolute_uri(f"/news/{news.id}/")}',
                from_email='noreply@newsportal.com',
                recipient_list=[news.author.email],
                fail_silently=True,
            )

    return redirect("news:news_detail", id=id)


from .models import Comment

def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id)

    if request.user == comment.user or request.user.is_superuser:
        comment.delete()

    return redirect("news:news_detail", id=comment.news.id)

@login_required
def reply_comment(request, id):

    parent_comment = Comment.objects.get(id=id)

    if request.method == "POST":
        text = request.POST.get("text")

        reply = Comment.objects.create(
            news=parent_comment.news,
            user=request.user,
            text=text,
            parent=parent_comment
        )

        # Send email notification to parent commenter if not the replier
        if parent_comment.user != request.user and parent_comment.user.email:
            send_mail(
                subject=f'New reply to your comment on: {parent_comment.news.title}',
                message=f'Hi {parent_comment.user.username},\n\n{request.user.username} replied to your comment:\n\n"{text}"\n\nView the article: {request.build_absolute_uri(f"/news/{parent_comment.news.id}/")}',
                from_email='noreply@newsportal.com',
                recipient_list=[parent_comment.user.email],
                fail_silently=True,
            )

    return redirect("news:news_detail", id=parent_comment.news.id)



@login_required
def bookmark_news(request, id):
    news = News.objects.get(id=id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        news=news
    )

    if not created:
        bookmark.delete()
        Notification.objects.create(
            user=request.user,
            news=news,
            message=f"Removed '{news.title}' from saved news."
        )
    else:
        Notification.objects.create(
            user=request.user,
            news=news,
            message=f"Saved '{news.title}' to your saved news."
        )

    return redirect(f"/news/{id}/")


@login_required
def saved_news(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    return render(request, "news/saved_news.html", {"bookmarks": bookmarks})


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "news/notifications.html", {"notifications": user_notifications})


@login_required
def mark_as_read(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('news:notifications')


def search_news(request):

    query = request.GET.get('q', '').strip()

    if query:
        results = News.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )
    else:
        results = News.objects.none()

    return render(request, "news/search_results.html", {
        "results": results,
        "query": query
    })



from .models import Follow

@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)

    if request.user == target_user:
        return redirect('accounts:profile', username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    if not created:
        follow.delete()  # unfollow

    return redirect('accounts:profile', username=username)



def profile(request, username):
    user_profile = get_object_or_404(User, username=username)

    # Keep your profile view data aligned with accounts.profile template expectations.
    user_news = News.objects.filter(author=user_profile)

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user_profile
        ).exists()

    followers_count = user_profile.followers.count() if hasattr(user_profile, 'followers') else 0
    following_count = user_profile.following.count() if hasattr(user_profile, 'following') else 0

    return render(request, 'accounts/profile.html', {
        'profile_user': user_profile,
        'user_news': user_news,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count
    })
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user_profile
        ).exists()

    followers_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    return render(request, 'accounts/profile.html', {
        'user_profile': user_profile,
        'user_news': user_news,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count
    })

import requests

def fetch_news():
    url = "https://newsapi.org/v2/top-headlines?country=in&apiKey=960001964a5e4cf9b2122df08373a39e"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "ok":
        return data.get("articles", [])
    else:
        print("API Error:", data)
        return []


def save_news():
    articles = fetch_news()

    print("TOTAL ARTICLES:", len(articles))  # Debugging line to check number of articles fetched

    for item in articles:
        if not News.objects.filter(title=item['title']).exists():
            News.objects.create(
                title=item['title'],
                content=item['description'] or "",
                author_id=1  # default admin
            )
