from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
import uuid
from .models import Booking, Payment
from .serializers import (
    BookingSerializer, BookingCreateSerializer, 
    PaymentSerializer
)
from users.permissions import IsCustomer, IsProvider, IsAdmin
from services.models import TimeSlot
from .reports import (
    generate_customer_bookings_pdf,
    generate_provider_bookings_pdf,
    generate_admin_stats_pdf,
    generate_invoice_pdf
)


class BookingViewSet(viewsets.ModelViewSet):   
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'service', 'provider', 'customer']
    search_fields = ['service__title', 'customer__username', 'provider__username']
    ordering_fields = ['booking_date', 'price_at_booking']
    ordering = ['-booking_date']
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomer()]
        if self.action in ['confirm', 'reject']:
            return [IsAuthenticated(), IsProvider()]
        if self.action == 'list':
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Booking.objects.all()
        if user.is_provider:
            return Booking.objects.filter(provider=user)
        if user.is_customer:
            return Booking.objects.filter(customer=user)
        return Booking.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slot_id = request.data.get('time_slot')
        
        if not slot_id:
            return Response(
                {'error': 'شناسه بازه زمانی الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            slot = TimeSlot.objects.select_for_update().get(id=slot_id)
        except TimeSlot.DoesNotExist:
            return Response(
                {'error': 'بازه زمانی یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not slot.is_active:
            return Response(
                {'error': 'این بازه زمانی فعال نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if slot.is_booked:
            return Response(
                {'error': 'این بازه زمانی قبلاً رزرو شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if slot.start_time < timezone.now():
            return Response(
                {'error': 'این بازه زمانی گذشته است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not slot.service.provider.is_active:
            return Response(
                {'error': 'ارائه‌دهنده این سرویس فعال نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = serializer.save(
            customer=request.user,
            provider=slot.service.provider,
            service=slot.service,
            time_slot=slot,
            price_at_booking=slot.service.price
        )
        
        slot.is_booked = True
        slot.save()
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        
        if request.user != booking.provider and not request.user.is_admin:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != Booking.Status.PENDING:
            return Response(
                {'error': 'این رزرو قابل تأیید نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.confirm()
        
        return Response({
            'message': 'رزرو با موفقیت تأیید شد',
            'booking': BookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        booking = self.get_object()
        
        if request.user != booking.provider and not request.user.is_admin:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != Booking.Status.PENDING:
            return Response(
                {'error': 'این رزرو قابل رد نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.reject()
        
        return Response({
            'message': 'رزرو رد شد',
            'booking': BookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        if request.user != booking.customer:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.can_cancel:
            return Response(
                {'error': 'مهلت لغو رزرو به پایان رسیده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.cancel(by_customer=True)
        
        return Response({
            'message': 'رزرو با موفقیت لغو شد',
            'booking': BookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['get'])
    def cancel_info(self, request, pk=None):
        booking = self.get_object()
        
        return Response({
            'can_cancel': booking.can_cancel,
            'cancel_deadline': booking.cancel_deadline,
            'time_remaining_seconds': booking.time_until_cancel_deadline.total_seconds(),
        })
    
    @action(detail=True, methods=['get'])
    def payment_info(self, request, pk=None):
        booking = self.get_object()
        
        return Response({
            'can_pay': booking.can_pay,
            'amount': booking.price_at_booking,
            'payment_status': booking.payment_status,
            'payment_date': booking.payment_date,
        })
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        user = request.user
        
        if user.is_customer:
            bookings = Booking.objects.filter(customer=user)
        elif user.is_provider:
            bookings = Booking.objects.filter(provider=user)
        elif user.is_admin:
            bookings = Booking.objects.all()
        else:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        
        if user.is_admin:
            queryset = Booking.objects.all()
        elif user.is_provider:
            queryset = Booking.objects.filter(provider=user)
        elif user.is_customer:
            queryset = Booking.objects.filter(customer=user)
        else:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'total': queryset.count(),
            'pending': queryset.filter(status=Booking.Status.PENDING).count(),
            'confirmed': queryset.filter(status=Booking.Status.CONFIRMED).count(),
            'completed': queryset.filter(status=Booking.Status.COMPLETED).count(),
            'canceled': queryset.filter(status=Booking.Status.CANCELED).count(),
            'rejected': queryset.filter(status=Booking.Status.REJECTED).count(),
            'paid': queryset.filter(payment_status=Booking.PaymentStatus.PAID).count(),
            'unpaid': queryset.filter(payment_status=Booking.PaymentStatus.UNPAID).count(),
        })
    
    
    @action(detail=False, methods=['get'])
    def export_customer_pdf(self, request):
        if not request.user.is_customer:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = Booking.objects.filter(customer=request.user)
        
        if not bookings.exists():
            return Response(
                {'error': 'هیچ رزروی برای شما وجود ندارد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pdf = generate_customer_bookings_pdf(request.user, bookings)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="customer_bookings_{timezone.now().date()}.pdf"'
        return response
    
    @action(detail=False, methods=['get'])
    def export_provider_pdf(self, request):
        if not request.user.is_provider:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = Booking.objects.filter(provider=request.user)
        
        if not bookings.exists():
            return Response(
                {'error': 'هیچ رزروی برای شما وجود ندارد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pdf = generate_provider_bookings_pdf(request.user, bookings)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="provider_bookings_{timezone.now().date()}.pdf"'
        return response
    
    @action(detail=False, methods=['get'])
    def export_admin_stats_pdf(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pdf = generate_admin_stats_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="admin_stats_{timezone.now().date()}.pdf"'
        return response
    
    @action(detail=True, methods=['get'])
    def export_invoice_pdf(self, request, pk=None):
        booking = self.get_object()
        
        if not (request.user == booking.customer or request.user == booking.provider or request.user.is_admin):
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.payment_status != Booking.PaymentStatus.PAID:
            return Response(
                {'error': 'این رزرو پرداخت نشده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf = generate_invoice_pdf(booking)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{booking.id}.pdf"'
        return response


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'is_successful']
    ordering = ['-payment_date']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Payment.objects.all()
        if user.is_provider:
            return Payment.objects.filter(booking__provider=user)
        if user.is_customer:
            return Payment.objects.filter(booking__customer=user)
        return Payment.objects.none()
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        booking_id = request.data.get('booking')
        
        if not booking_id:
            return Response(
                {'error': 'شناسه رزرو الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        if request.user != booking.customer:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.can_pay:
            return Response(
                {'error': 'امکان پرداخت وجود ندارد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if Payment.objects.filter(booking=booking).exists():
            return Response(
                {'error': 'این رزرو قبلاً پرداخت شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction_id = str(uuid.uuid4()).replace('-', '')[:16]
        
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.price_at_booking,
            transaction_id=transaction_id,
            is_successful=True,
            card_number=request.data.get('card_number', ''),
            card_holder_name=request.data.get('card_holder_name', '')
        )
        
        booking.mark_paid()
        
        return Response({
            'message': f'پرداخت با موفقیت انجام شد. شماره تراکنش: {transaction_id}',
            'payment': PaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)