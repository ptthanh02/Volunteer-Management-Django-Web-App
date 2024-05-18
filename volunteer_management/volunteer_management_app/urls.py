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
    path('dang-ky/', views.user_register, name='user_register'),
    path('dang-xuat/', views.user_logout, name='user_logout'),
    path('tai_len/', views.custom_upload_function, name="custom_upload_file"),
    path('yeu-thich-hoat-dong/', views.like_event, name='like_event'),
    path('load-events/', views.load_events, name='load_events'),
    path('filter-events/', views.filter_events, name='filter_events'),
    path('share-event/', views.share_event, name='share_event'),
    path('reset_events_filter/', views.reset_events_filter, name='reset_events_filter'),
    path('hoat-dong-tinh-nguyen/<int:event_id>/', views.event_detail, name='event_detail'),
    path('tham-gia-hoat-dong/', views.join_event, name='join_event'),
    path('quyen-gop/', views.donation, name='donation'),
    path('bao-cao-hoat-dong/', views.activity_reports , name='activity_reports'),
    path('bao-cao-hoat-dong/<int:event_id>/', views.activity_report_detail, name='activity_report_detail'),
    path('admin/volunteer_management_app/eventreport/<int:report_id>/change/', views.admin_eventreport_change, name='admin_eventreport_change'),
    path('cap-nhat-thong-tin/', views.update_profile, name='update_profile'),
    path('doi-mat-khau/', views.change_password, name='change_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)