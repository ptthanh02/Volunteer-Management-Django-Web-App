from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .forms import *

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
    list_display = ['name', 'start_date', 'end_date', 'location', 'hours', 'organizer', 'status']
    list_filter = ['start_date']
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
        ('Thông tin sự kiện', {'fields': ('name', 'start_date', 'end_date', 'location', 'description', 'hours', 'organizer', 'status')}),
    )

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'name', 'age', 'email', 'phone', 'hours_worked', 'is_active']
    list_filter = ['is_active']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=False, is_staff=False)
    
    fieldsets = (
        ('Thông tin tài khoản', {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('name', 'age', 'email', 'phone', 'address',  'skills', 'hours_worked')}),
        ('Quyền hạn', {'fields': ('is_active',)}),
        ('Ngày đăng nhập cuối', {'fields': ('last_login',)}),
    )
    search_fields = ('username', 'name', 'age', 'email', 'phone', 'address', 'skills')
    ordering = ('id',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'age', 'email', 'phone', 'address', 'skills', 'hours_worked', 'password1', 'password2', 'is_active')}
        ),
    )
    filter_horizontal = ()
        
class AdminUserAdmin(UserAdmin):
    list_display = ['username', 'name', 'email' ,'is_superuser', 'is_active']
    list_filter = ['is_superuser', 'is_active']
    search_fields = ['username', 'name', 'email']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=True)

    fieldsets = (
        ('Thông tin tài khoản', {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('name', 'age', 'email', 'phone', 'address',  'skills', 'hours_worked')}),
        ('Quyền hạn', {'fields': ('is_staff', 'is_active')}),
        ('Ngày đăng nhập cuối', {'fields': ('last_login',)}),
    )
    search_fields = ('username', 'name', 'age', 'email', 'phone', 'address', 'skills')
    ordering = ('id',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'age', 'email', 'phone', 'address', 'skills', 'hours_worked', 'password1', 'password2', 'is_staff', 'is_superuser' ,'is_active')}
        ),
    )
    filter_horizontal = ()
    
class EventReportAdmin(admin.ModelAdmin):
    list_display = ['event', 'report_date', 'participants_count', 'author']
    list_filter = ['event', 'report_date']
    search_fields = ['event__name', 'report_content']
    
    fieldsets = (
        (None, {
            'fields': ('event', 'participants_count')
        }),
        ('Nội dung báo cáo', {
            'fields': ('report_content',)
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

admin.site.register(EventReport, EventReportAdmin)
admin.site.register(VolunteerEventPost, VolunteerEventPostAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AdminUser, AdminUserAdmin)