from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from django.db.models import F
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field
from datetime import timedelta

class VolunteerEventPost(models.Model):
    name = models.CharField(_('Tên sự kiện'), max_length=50, null=False, blank=False)
    start_date = models.DateField(_('Ngày tổ chức'), null=False, blank=False)
    duration = models.PositiveIntegerField(_('Thời hạn (ngày)'), default=10)
    location = models.CharField(_('Địa điểm'), max_length=100, null=False, blank=False)
    description = CKEditor5Field(_('Mô tả'), null=False, blank=False, config_name='extends')
    hours = models.IntegerField(_('Số giờ tình nguyện'), null=False, blank=False)
    likes = models.IntegerField(_('Lượt yêu thích'), default=0, editable=False)
    shares = models.IntegerField(_('Lượt chia sẻ'), default=0, editable=False)
    participants = models.IntegerField(_('Số người tham gia'), default=0)
    STATUS_CHOICES = [
        ('planned', _('Đang lên kế hoạch')),
        ('ongoing', _('Đang diễn ra')),
        ('completed', _('Đã kết thúc')),
    ]
    status = models.CharField(
        _('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='planned'
    )
    
    def get_end_date(self):
        return self.date + timedelta(days=self.duration)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Sự kiện tình nguyện')
        verbose_name_plural = _('Sự kiện tình nguyện')
        ordering = ['start_date']

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('Phải có tên đăng nhập'))
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=30, unique=True,
                        help_text=_('Yêu cầu 30 ký tự hoặc ít hơn. Chỉ chứa chữ cái, số và các ký tự @/./+/-/_'),
                        error_messages={
                            'unique': _("Tên đăng nhập đã tồn tại."),
                        },
                        null=False, blank=False
                        )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Chỉ định người dùng có tất cả các quyền quản trị hệ thống.'
        ), 
    )                                              
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Chỉ định người dùng có quyền truy cập vào trang quản trị (admin).'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Chỉ định người dùng được coi là "active". Hủy chọn để vô hiệu hóa tài khoản này.'
        ),
    )
    USERNAME_FIELD = 'username'
    objects = CustomUserManager()
    
    avatar = models.ImageField(_('Ảnh đại diện'), upload_to='avatars/', null=True, blank=True)
    name = models.CharField(_('Tên'), max_length=30, null=False, blank=False)
    age = models.IntegerField(_('Tuổi'), null=False, blank=False)
    email = models.EmailField(_('Email'), null=True, blank=True, unique=True)
    phone = models.CharField(_('Số điện thoại'), max_length=15, null=True, blank=True)
    address = models.CharField(_('Địa chỉ'), max_length=100, null=True, blank=True)
    skills = models.CharField(_('Kỹ năng'), max_length=100, null=True, blank=True)
    hours_worked = models.IntegerField(_('Số giờ tình nguyện'), default=0)
    liked_events = models.ManyToManyField(VolunteerEventPost, related_name='liked_users', blank=True, verbose_name=_('Sự kiện yêu thích'))
    events_attended = models.ManyToManyField(VolunteerEventPost, related_name='attendees', blank=True, verbose_name=_('Sự kiện đã tham gia'))
    
    REQUIRED_FIELDS = ['name', 'age']

    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')
        ordering = ['username']
        

