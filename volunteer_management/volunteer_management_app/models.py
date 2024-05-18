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
from django.contrib.auth import get_user
from django.conf import settings
from functools import cached_property

class VolunteerEventPost(models.Model):
    name = models.CharField(_('Tên sự kiện'), max_length=500, null=False, blank=False)
    start_date = models.DateTimeField(_('Ngày tổ chức'), null=False, blank=False)
    end_date = models.DateTimeField(_('Ngày kết thúc'), null=False, blank=False)
    location = models.CharField(_('Địa điểm'), max_length=100, null=False, blank=False)
    description = CKEditor5Field(_('Mô tả sự kiện'), null=False, blank=False, config_name='extends', help_text=_('Mô tả chi tiết về sự kiện, đây cũng sẽ là nội dụng  cho bài viết về sự kiện tình nguyện này.'))
    hours = models.IntegerField(_('Số giờ tình nguyện'), null=False, blank=False, default=1, help_text=_('Số giờ tối thiểu mà người tham gia cần tình nguyện.'))
    cover = models.ImageField(_('Ảnh bìa sự kiện'), upload_to='event_covers/', null=True, blank=True, default='event_covers/default_cover.png')
    likes = models.IntegerField(_('Lượt yêu thích'), default=0)
    shares = models.IntegerField(_('Lượt chia sẻ'), default=0)
    views = models.IntegerField(_('Lượt xem'), default=0)
    max_participants = models.IntegerField(_('Số người tham gia tối đa'), default=50)
    current_participants = models.IntegerField(_('Số người tham gia hiện tại'), default=0)
    organizer = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='events_organized', verbose_name=_('Người tổ chức'), help_text=_('Chỉ người dùng quản trị mới có thể tổ chức sự kiện.'), null=False, blank=False)
    STATUS_CHOICES = [
        ('planned', _('Đang lên kế hoạch')),
        ('ongoing', _('Đang diễn ra')),
        ('completed', _('Đã kết thúc')),
    ]
    status = models.CharField(
        _('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='planned'
    )
    CATEGORY_CHOICES = [
        ('education', _('Giáo dục')),
        ('environment', _('Môi trường')),
        ('health', _('Y tế')),
        ('community', _('Cộng đồng')),
        ('other', _('Khác')),
    ]
    category = models.CharField(
        _('Loại sự kiện'),
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
    )
    
    def update_status(self):
        now = timezone.now()
        if self.start_date > now:
            self.status = 'planned'
        elif self.start_date <= now <= self.end_date:
            self.status = 'ongoing'
        else:
            self.status = 'completed'

    def clean(self):
        now =  timezone.now()
        if self.hours < 1:
            raise ValidationError(_('Số giờ tình nguyện phải lớn hơn hoặc bằng 1.'))

        if self.start_date is None:
            raise ValidationError(_('Ngày tổ chức không được để trống.'))

        if self.end_date is None:
            raise ValidationError(_('Ngày kết thúc không được để trống.'))
        else:
            if self.end_date <= self.start_date:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu.'))
            
    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Sự kiện tình nguyện')
        verbose_name_plural = _('Sự kiện tình nguyện')
        ordering = ['start_date']

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
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
        _('Quản trị hệ thống'),
        default=False,
        help_text=_(
            'Chỉ định người dùng có tất cả các quyền quản trị hệ thống.'
        ), 
    )                                              
    is_staff = models.BooleanField(
        _('Nhân viên hệ thống'),
        default=False,
        help_text=_('Chỉ định người dùng có quyền truy cập vào trang quản trị (admin).'),
    )
    is_active = models.BooleanField(
        _('Trạng thái hoạt động'),
        default=True,
        help_text=_(
            'Chỉ định người dùng được coi là "active". Hủy chọn để vô hiệu hóa tài khoản này.'
        ),
    )
    USERNAME_FIELD = 'username'
    objects = CustomUserManager()
    
    avatar = models.ImageField(_('Ảnh đại diện'), upload_to='avatars/', null=True, blank=True, default='avatars/default_avatar.png')
    name = models.CharField(_('Tên'), max_length=30, null=False, blank=False)
    age = models.IntegerField(_('Tuổi'), null=True, blank=True)
    email = models.EmailField(_('Email'), null=True, blank=True, unique=True)
    phone = models.CharField(_('Số điện thoại'), max_length=15, null=True, blank=True)
    address = models.CharField(_('Địa chỉ'), max_length=100, null=True, blank=True)
    skills = models.CharField(_('Kỹ năng, sở thích'), max_length=100, null=True, blank=True)
    hours_worked = models.IntegerField(_('Số giờ tình nguyện'), default=0, blank=True, null=True)
    viewed_events = models.ManyToManyField(VolunteerEventPost, through='UserEventRelation', related_name='viewed_users', blank=True, verbose_name=_('Sự kiện đã xem'))
    liked_events = models.ManyToManyField(VolunteerEventPost, through='UserEventRelation', related_name='liked_users', blank=True, verbose_name=_('Sự kiện yêu thích'))
    events_attended = models.ManyToManyField(VolunteerEventPost, through='UserEventRelation', related_name='attendees', blank=True, verbose_name=_('Sự kiện đã tham gia'))
    viewed_reports = models.ManyToManyField('EventReport', through='UserEventRelation', related_name='viewed_users', blank=True, verbose_name=_('Báo cáo sự kiện đã xem'))

    REQUIRED_FIELDS = ['name', 'phone']
    
    @property
    def viewed_events(self):
        return self.event_relations.filter(relation_type=1).values_list('event')

    @cached_property
    def liked_events(self):
        return self.event_relations.filter(relation_type=2).values_list('event', flat=True)

    @property
    def events_attended(self):
        return self.event_relations.filter(relation_type=3).values_list('event')

    @property
    def viewed_reports(self):
        return self.event_relations.filter(relation_type=4).values_list('event_report')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')
        ordering = ['name']
        

class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Người dùng quản trị'
        verbose_name_plural = 'Người dùng quản trị'
        
class EventReport(models.Model):
    event = models.ForeignKey(VolunteerEventPost, on_delete=models.CASCADE, related_name='reports', verbose_name=_('Sự kiện'), help_text=_('Chỉ có thể báo cáo những sự kiện đã kết thúc mà đã bạn tổ chức.'), null=False, blank=False)
    report_date = models.DateField(_('Ngày báo cáo'), auto_now_add=True)
    participants_count = models.PositiveIntegerField(_('Số người tham gia'), default=0, help_text=_('Số người thực sự đã tham gia sự kiện này. (Có thể biết qua điểm danh)'))  
    report_content = CKEditor5Field(_('Nội dung báo cáo'), config_name='extends')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports', verbose_name=_('Người báo cáo'))
       
    class Meta:
        verbose_name = _('Báo cáo sự kiện')
        verbose_name_plural = _('Báo cáo sự kiện')
        ordering = ['-report_date']
        
    def clean(self):
        # if self.participants_count < 0:
        #     raise ValidationError(_('Số người tham gia không thể âm.'))
        # if self.participants_count > self.event.current_participants:
        #     raise ValidationError(_('Số người tham gia không thể lớn hơn số người tham gia hiện tại của sự kiện.'))
        if self.event.status != 'completed':
            raise ValidationError(_('Chỉ có thể báo cáo khi sự kiện đã kết thúc.'))
        if self in self.event.reports.all():
            raise ValidationError(_('Báo cáo này đã tồn tại.'))

    def __str__(self):
        return f"Báo cáo sự kiện '{self.event.name}' ngày {self.report_date}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Nếu là báo cáo mới
            self.author = self.event.organizer
        super().save(*args, **kwargs)

class UserEventRelation(models.Model):
    RELATION_TYPES = (
        ('viewed', 'Đã xem'),
        ('liked', 'Đã thích'),
        ('attended', 'Đã tham dự'),
        ('reported', 'Đã báo cáo'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_relations', verbose_name='Người dùng')
    event = models.ForeignKey(VolunteerEventPost, on_delete=models.CASCADE, related_name='user_relations', verbose_name='Sự kiện')
    event_report = models.ForeignKey(EventReport, on_delete=models.CASCADE, null=True, blank=True, related_name='user_relations', verbose_name='Báo cáo sự kiện')
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPES, verbose_name='Hoạt động', default='viewed')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Thời gian cập nhật')

    class Meta:
        verbose_name = 'Hoạt động người dùng - sự kiện'
        verbose_name_plural = 'Hoạt động người dùng - sự kiện'