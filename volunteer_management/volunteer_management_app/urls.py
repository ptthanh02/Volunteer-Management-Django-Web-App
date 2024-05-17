from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='trang-chu/')),
    path('trang-chu/', views.homepage, name='homepage'),
    path('hoat-dong/', views.activities, name='activities'),
    path('dang-nhap/', views.user_login, name='user_login'),
    path('dangxuat/', views.user_logout, name='user_logout'),
    path('dang-ky/', views.user_register, name='user_register'),
    path('tai_len/', views.custom_upload_function, name="custom_upload_file"),
    path('yeu-thich-su-kien/', views.like_event, name='like_event'),
    path('load-events/', views.load_events, name='load_events'),
    path('filter-events/', views.filter_events, name='filter_events'),
    path('share-event/', views.share_event, name='share_event'),
    path('reset_events_filter/', views.reset_events_filter, name='reset_events_filter'),
    path('hoat-dong-tinh-nguyen/<int:event_id>/', views.event_detail, name='event_detail'),
    path('yeu-thich-su-kien-detail/', views.like_event_detail, name='like_event_detail'),
    path('tham-gia-su-kien/', views.join_event, name='join_event'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)