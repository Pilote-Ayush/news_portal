from .models import User

def notifications_count(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
    else:
        unread_count = 0
    return {
        'unread_notifications': unread_count
    }
