from django.shortcuts import render
from django.core.paginator import Paginator
from news.models import News, Comment
from django.db.models import Q, Count

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

def home(request):
    search = request.GET.get('search')
    category = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    author = request.GET.get('author')
    sort_by = request.GET.get('sort_by', 'newest')

    news_list = News.objects.filter(is_approved=True).order_by('-created_at')
    trending_news = News.objects.filter(is_trending=True, is_approved=True).order_by('-created_at')[:5]
    breaking_news = News.objects.filter(breaking=True, is_approved=True).order_by('-created_at')[:5]

    # Filters
    if search:
        news_list = news_list.filter(Q(title__icontains=search) | Q(content__icontains=search))

    if category and category != 'All':
        news_list = news_list.filter(category__name__icontains=category)

    if date_from:
        news_list = news_list.filter(created_at__date__gte=date_from)

    if date_to:
        news_list = news_list.filter(created_at__date__lte=date_to)

    if author:
        news_list = news_list.filter(author__username__icontains=author)

    # Sorting
    if sort_by == 'most_liked':
        news_list = news_list.annotate(like_count=Count('likes')).order_by('-like_count')
    elif sort_by == 'most_viewed':
        news_list = news_list.order_by('-views')
    else:  # newest
        news_list = news_list.order_by('-created_at')

    # Pagination
    paginator = Paginator(news_list, 12)  # 12 news per page
    page_number = request.GET.get('page')
    news = paginator.get_page(page_number)

    # Recent comments: prefer current user comments, else most recent site-wide
    if request.user.is_authenticated:
        recent_comments = Comment.objects.filter(user=request.user).order_by('-created_at')[:3]
    else:
        recent_comments = Comment.objects.order_by('-created_at')[:3]

    return render(request, 'home.html', {
        'news': news,
        'trending_news': trending_news,
        'breaking_news': breaking_news,
        'recent_comments': recent_comments,
    })