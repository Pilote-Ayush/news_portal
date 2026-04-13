from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('create/', views.create_news, name='create_news'),
    path('edit/<int:id>/', views.edit_news, name='edit_news'),
    path('delete/<int:id>/', views.delete_news, name='delete_news'),
    path('like/<int:id>/', views.like_news, name='like_news'),
    path('comment/<int:id>/', views.add_comment, name='add_comment'),
    path('comment/reply/<int:id>/', views.reply_comment, name='reply_comment'),
    path('comment/delete/<int:id>/', views.delete_comment, name='delete_comment'),
    path('bookmark/<int:id>/', views.bookmark_news, name='bookmark_news'),
    path('saved/', views.saved_news, name='saved_news'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:id>/', views.mark_as_read, name='mark_as_read'),
    path('approve/<int:id>/', views.approve_news, name='approve_news'),
    path('search/', views.search_news, name='search_news'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('<int:id>/', views.news_detail, name='news_detail'),
]