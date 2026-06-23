# bookings/serializers.py
from rest_framework import serializers
from .models import Booking, Payment
from services.models import Service, TimeSlot


class BookingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    time_slot_start = serializers.DateTimeField(source='time_slot.start_time', read_only=True)
    time_slot_end = serializers.DateTimeField(source='time_slot.end_time', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    can_cancel = serializers.ReadOnlyField()
    can_pay = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'customer_name', 'provider', 'provider_name',
            'service', 'service_title', 'time_slot', 'time_slot_start', 'time_slot_end',
            'status', 'status_display', 'payment_status', 'payment_status_display',
            'price_at_booking', 'booking_date', 'payment_date', 'confirmed_date', 'canceled_date',
            'customer_note', 'provider_note', 'can_cancel', 'can_pay'
        ]
        read_only_fields = [
            'id', 'booking_date', 'payment_date', 'confirmed_date', 'canceled_date',
            'customer', 'provider', 'service', 'price_at_booking'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    time_slot = serializers.PrimaryKeyRelatedField(queryset=TimeSlot.objects.all())
    
    class Meta:
        model = Booking
        fields = ['time_slot', 'customer_note']


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    booking_service_title = serializers.CharField(source='booking.service.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_id', 'booking_service_title',
            'amount', 'transaction_id', 'is_successful', 'payment_date',
            'card_number', 'card_holder_name'
        ]
        read_only_fields = ['id', 'transaction_id', 'payment_date', 'is_successful']


class PaymentCreateSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    card_number = serializers.CharField(max_length=16, required=True)
    card_holder_name = serializers.CharField(max_length=100, required=True)
    
    class Meta:
        model = Payment
        fields = ['booking', 'card_number', 'card_holder_name']