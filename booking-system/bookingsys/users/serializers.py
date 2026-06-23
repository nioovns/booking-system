# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db.models import Count, Sum
from .models import User
from services.models import Service
from bookings.models import Booking


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'role_display', 'avatar',
            'is_admin', 'is_provider', 'is_customer'
        ]
        read_only_fields = ['id', 'is_admin', 'is_provider', 'is_customer']


class UserCreateSerializer(serializers.ModelSerializer):    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role', 'avatar'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "رمز عبور و تأیید آن مطابقت ندارند"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'avatar'
        ]
    
    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است")
        return value
    
    def validate_phone_number(self, value):
        if value and User.objects.exclude(pk=self.instance.pk).filter(phone_number=value).exists():
            raise serializers.ValidationError("این شماره موبایل قبلاً ثبت شده است")
        return value


class ChangePasswordSerializer(serializers.Serializer):    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("رمز عبور فعلی اشتباه است")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "رمز عبور جدید و تأیید آن مطابقت ندارند"})
        return data


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'role', 'role_display', 'is_active', 'date_joined']


class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    admin_count = serializers.IntegerField()
    provider_count = serializers.IntegerField()
    customer_count = serializers.IntegerField()
    active_users = serializers.IntegerField()
    
    total_services = serializers.IntegerField()
    active_services = serializers.IntegerField()
    inactive_services = serializers.IntegerField()
    
    total_bookings = serializers.IntegerField()
    today_bookings = serializers.IntegerField()
    week_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    
    total_income = serializers.IntegerField()
    today_income = serializers.IntegerField()
    week_income = serializers.IntegerField()
    
    daily_bookings = serializers.JSONField()
    monthly_income = serializers.JSONField()
    role_distribution = serializers.JSONField()
    booking_status = serializers.JSONField()
    service_status = serializers.JSONField()
    top_services = serializers.ListField()


class ProviderDashboardSerializer(serializers.Serializer):
    total_services = serializers.IntegerField()
    active_services = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    total_income = serializers.IntegerField()
    monthly_bookings = serializers.JSONField()
    popular_services = serializers.ListField()


class CustomerDashboardSerializer(serializers.Serializer):
    total_bookings = serializers.IntegerField()
    upcoming_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    total_spent = serializers.IntegerField()
    recent_bookings = serializers.ListField()