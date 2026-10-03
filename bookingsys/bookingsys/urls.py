from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="سیستم مدیریت و رزرو خدمات API",
        default_version='v1',
        description="مستندات API پروژه سیستم مدیریت و رزرو خدمات",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # APIها
    path('api/users/', include('users.urls')),
    path('api/services/', include('services.urls')),
    path('api/bookings/', include('bookings.urls')),

    # مستندات
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # ========== صفحات HTML (فرانت‌اند) ==========
    path('', TemplateView.as_view(template_name='login.html'), name='home'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    
    # صفحات ادمین
    path('admin-dashboard/', TemplateView.as_view(template_name='admin-dashboard.html'), name='admin_dashboard'),
    path('admin-users/', TemplateView.as_view(template_name='admin-users.html'), name='admin_users'),
    path('admin-services/', TemplateView.as_view(template_name='admin-services.html'), name='admin_services'),
    path('admin-bookings/', TemplateView.as_view(template_name='admin-bookings.html'), name='admin_bookings'),
    path('admin-reports/', TemplateView.as_view(template_name='admin-reports.html'), name='admin_reports'),
    
    # صفحات ارائه‌دهنده
    path('provider-services/', TemplateView.as_view(template_name='provider-services.html'), name='provider_services'),
    path('provider-timeslots/', TemplateView.as_view(template_name='provider-timeslots.html'), name='provider_timeslots'),
    path('provider-bookings/', TemplateView.as_view(template_name='provider-bookings.html'), name='provider_bookings'),
    path('provider-profile/', TemplateView.as_view(template_name='provider-profile.html'), name='provider_profile'),
    
    # صفحات مشتری
    path('customer-services/', TemplateView.as_view(template_name='customer-services.html'), name='customer_services'),
    path('customer-service-detail/', TemplateView.as_view(template_name='customer-service-detail.html'), name='customer_service_detail'),
    path('customer-booking/', TemplateView.as_view(template_name='customer-booking.html'), name='customer_booking'),
    path('customer-bookings/', TemplateView.as_view(template_name='customer-bookings.html'), name='customer_bookings'),
    path('customer-payment/', TemplateView.as_view(template_name='customer-payment.html'), name='customer_payment'),
    path('customer-profile/', TemplateView.as_view(template_name='customer-profile.html'), name='customer_profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)