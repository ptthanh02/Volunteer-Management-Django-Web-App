from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='trang-chu/')),
    path('trang-chu/', views.homepage, name='homepage'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)