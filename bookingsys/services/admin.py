# services/admin.py
from django.contrib import admin
from .models import Category, Service, TimeSlot


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'price', 'duration_minutes', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'provider__username')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('service', 'start_time', 'end_time', 'is_booked', 'is_active')
    list_filter = ('is_booked', 'is_active')
    