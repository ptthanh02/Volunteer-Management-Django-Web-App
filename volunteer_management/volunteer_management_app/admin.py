from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'name', 'age', 'email', 'phone', 'hours_worked', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
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
            'fields': ('username', 'name', 'age', 'email', 'phone', 'address', 'skills', 'hours_worked', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    filter_horizontal = ()
    
class VolunteerEventPostAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'get_end_date', 'location', 'get_description', 'hours', 'status']
    list_filter = ['start_date']
    search_fields = ['name', 'location', 'description']
    ordering = ['-start_date']
    
    def get_end_date(self, obj):
        return obj.start_date + timedelta(days=obj.duration)
    get_end_date.short_description = 'Ngày kết thúc'

    def get_description(self, obj):
        return obj.description[:50]  

    get_description.short_description = 'Mô tả' 

admin.site.register(VolunteerEventPost, VolunteerEventPostAdmin)
admin.site.register(CustomUser, CustomUserAdmin)