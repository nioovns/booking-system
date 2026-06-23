from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'get_full_name', 'email', 'phone_number', 'role_badge', 'is_active', 'date_joined')
    list_display_links = ('id', 'username')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    list_per_page = 20
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('اطلاعات شخصی'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('نقش و دسترسی‌ها'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('تاریخ‌های مهم'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
        
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',     
            'service_provider': '#28a745',  
            'customer': '#007bff',  
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = _('نقش')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('نام کامل')
    get_full_name.admin_order_field = 'first_name'
    
    actions = ['make_active', 'make_inactive', 'make_provider', 'make_customer', 'make_admin']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کاربر فعال شدند.')
    make_active.short_description = 'فعال کردن کاربران انتخاب شده'
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کاربر غیرفعال شدند.')
    make_inactive.short_description = 'غیرفعال کردن کاربران انتخاب شده'
    
    def make_provider(self, request, queryset):
        updated = queryset.update(role=User.Roles.SERVICE_PROVIDER)
        self.message_user(request, f'{updated} کاربر به ارائه‌دهنده تبدیل شدند.')
    make_provider.short_description = 'تبدیل به ارائه‌دهنده'
    
    def make_customer(self, request, queryset):
        updated = queryset.update(role=User.Roles.CUSTOMER)
        self.message_user(request, f'{updated} کاربر به مشتری تبدیل شدند.')
    make_customer.short_description = 'تبدیل به مشتری'
    
    def make_admin(self, request, queryset):
        updated = queryset.update(role=User.Roles.ADMIN)
        self.message_user(request, f'{updated} کاربر به ادمین تبدیل شدند.')
    make_admin.short_description = 'تبدیل به ادمین'