from rest_framework import serializers
from .models import Category, Service, TimeSlot


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_display = serializers.ReadOnlyField()
    duration_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'provider_name', 'category', 'category_name',
            'title', 'description', 'price', 'price_display', 'duration_minutes',
            'duration_display', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'provider']


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['title', 'description', 'price', 'duration_minutes', 'category', 'is_active']


class TimeSlotSerializer(serializers.ModelSerializer):
    service_title = serializers.SerializerMethodField()
    start_time_str = serializers.SerializerMethodField()
    end_time_str = serializers.SerializerMethodField()
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'service', 'service_title', 'start_time', 'start_time_str',
            'end_time', 'end_time_str', 'is_booked', 'is_active'
        ]
    
    def get_service_title(self, obj):
        if hasattr(obj, 'service') and obj.service:
            return obj.service.title
        return None
    
    def get_start_time_str(self, obj):
        if hasattr(obj, 'start_time') and obj.start_time:
            return obj.start_time.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_end_time_str(self, obj):
        if hasattr(obj, 'end_time') and obj.end_time:
            return obj.end_time.strftime('%Y/%m/%d %H:%M')
        return None