from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from django.utils.html import format_html

def staff_users(self, obj):
    User = get_user_model()
    return User.objects.filter(is_staff=True)

def is_event_organizer(user, event):
    if not user.is_authenticated:
        return False
    try:
        custom_user = user.customuser
        return custom_user == event.organizer
    except User.customuser.RelatedObjectDoesNotExist:
        return False

class VolunteerEventPostAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'location', 'hours', 'organizer', 'category', 'status']
    list_filter = ['start_date', 'end_date', 'category', 'status']
    search_fields = ['name', 'location', 'description']
    ordering = ['-start_date']
    search_fields = ['name', 'location', 'description']
    
    def staff_users(self, obj):
        User = get_user_model()
        return User.objects.filter(is_staff=True)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['organizer'].queryset = staff_users(self, obj)
        return form
    
    fieldsets = (
        ('Thông tin cơ bản', {'fields': ('name','organizer', 'category', 'status')}),
        ('Thời gian và địa điểm', {'fields': ('start_date', 'end_date', 'location')}),
        ('Chi tiết sự kiện', {'fields': ('cover', 'description', 'hours')}),
    )
    
class UserEventRelationInline(admin.TabularInline):
    model = UserEventRelation
    extra = 0
    can_delete = False
    fields = ('event', 'event_report','relation_type', 'updated_at')
    readonly_fields = ('event', 'event_report', 'relation_type', 'updated_at')
    
    def has_add_permission(self, request, obj=None):
        return False

    def relation_type(self, obj):
        return obj.get_relation_type_display()
    relation_type.short_description = 'Hoạt động'

    def event(self, obj):
        return obj.event.title
    event.short_description = 'Sự kiện'

    def event_report(self, obj):
        return obj.event_report.title if obj.event_report else ''
    event_report.short_description = 'Báo cáo sự kiện'
    

class CustomUserAdmin(UserAdmin):
    inlines = [UserEventRelationInline]
    list_display = ['username', 'name', 'age', 'email', 'phone', 'hours_worked', 'get_number_of_events_attended', 'is_active', 'thumbnail']
    list_filter = ['is_active']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=False, is_staff=False)
    
    fieldsets = (
        ('Thông tin tài khoản', {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('name', 'age', 'avatar',  'email', 'phone', 'address',  'skills')}),
        ('Thông tin tình nguyện viên', {'fields': ('hours_worked',)}),
        ('Quyền hạn', {'fields': ('is_active', 'is_superuser')}),
        ('Ngày đăng nhập cuối', {'fields': ('last_login',)}),
    )
    search_fields = ('username', 'name', 'age', 'email', 'phone', 'address', 'skills')
    ordering = ('id',)
    filter_horizontal = ()
    
    def thumbnail(self, object):
        if object.avatar:
            return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.avatar.url))
        return 'No Image'

    thumbnail.short_description = 'Avatar'
    
    def get_number_of_events_attended(self, obj):
        return obj.events_attended.count()
    get_number_of_events_attended.short_description = 'Số sự kiện đã tham gia'
        
class AdminUserAdmin(UserAdmin):
    inlines = [UserEventRelationInline]
    list_display = ['username', 'name', 'age', 'email', 'phone' ,'is_superuser', 'is_active' ,'get_number_of_events_hosted']
    list_filter = ['is_superuser', 'is_active']
    search_fields = ['username', 'name', 'email']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=True)

    fieldsets = (
        ('Thông tin tài khoản', {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('name', 'age', 'avatar', 'email', 'phone', 'address',  'skills')}),
        ('Thông tin tình nguyện viên', {'fields': ('hours_worked',)}),
        ('Quyền hạn', {'fields': ('is_active', 'is_superuser')}),
        ('Ngày đăng nhập cuối', {'fields': ('last_login',)}),
    )
    search_fields = ('username', 'name', 'age', 'email', 'phone', 'address', 'skills')
    ordering = ('id',)
    filter_horizontal = ()
    
    def get_number_of_events_hosted(self, obj):
        return VolunteerEventPost.objects.filter(organizer=obj).count()
    get_number_of_events_hosted.short_description = 'Số sự kiện đã tổ chức'
    
class EventReportAdmin(admin.ModelAdmin):
    list_display = ['event', 'report_date', 'participants_count', 'author']
    list_filter = ['report_date']
    search_fields = ['event__name', 'report_content']
    
    fieldsets = (
        ('Sự kiện báo cáo', {
            'fields': ('event',)
        }),
        ('Chi tiết báo cáo', {
            'fields': ('report_content', 'participants_count')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(event__organizer=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'event':
            kwargs['queryset'] = VolunteerEventPost.objects.filter(organizer=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # def has_delete_permission(self, request, obj=None):
    #     return False
    
admin.site.site_header = 'Tổ chức tình nguyện IUH'
admin.site.site_title = 'Quản lý tình nguyện viên IUH'
admin.site.index_title = 'Hệ thống quản lý tình nguyện viên IUH'
# admin.site.unregister(Group)
admin.site.register(EventReport, EventReportAdmin)
admin.site.register(VolunteerEventPost, VolunteerEventPostAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AdminUser, AdminUserAdmin)

