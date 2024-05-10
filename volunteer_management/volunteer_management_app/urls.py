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
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)